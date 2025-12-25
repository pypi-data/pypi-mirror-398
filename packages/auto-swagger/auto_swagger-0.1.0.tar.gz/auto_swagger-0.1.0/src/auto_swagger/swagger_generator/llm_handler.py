import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
from typing import List, Optional, Dict, Any
from .models import Change
from .generator_config import LLMConfig
import json
import re
import threading
import time
    
STOP_TOKEN = "<|endofjsdoc|>"

class LLMHandler:
    """Handles all LLM operations for generating swagger documentation."""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.device = torch.device("mps" if torch.backends.mps.is_available() else 
                            ("cuda" if torch.cuda.is_available() else "cpu"))

        self.tokenizer = AutoTokenizer.from_pretrained(
            config.model_name,
            trust_remote_code=True
        )
        
        # Check if tokenizer supports system role in chat template
        self.supports_system_role = self._check_system_role_support()
        
        # Add special tokens
        special_tokens_dict = {'additional_special_tokens': [STOP_TOKEN]}
        self.tokenizer.add_special_tokens(special_tokens_dict)
        self.tokenizer.pad_token = "[PAD]"
        self.tokenizer.padding_side = "left"
        
        
        # Determine appropriate dtype
        dtype = torch.float16 if self.device.type in ["cuda", "mps"] else torch.float32
        
        # Load the base causal LM with memory optimizations
        # For MPS, load on CPU first to avoid issues with resize_token_embeddings
        load_device_map = "cpu" if self.device.type == "mps" else "auto"
        base_model = AutoModelForCausalLM.from_pretrained(
            config.model_name,
            trust_remote_code=True,
            torch_dtype=dtype,
            device_map=load_device_map,
            low_cpu_mem_usage=True,
            load_in_8bit=False,
        )
        
        # Resize embeddings to handle new tokens
        # MPS doesn't support cholesky operation in resize_token_embeddings
        # So we do resize on CPU, then move to MPS
        if self.device.type == "mps":
            print("Resizing embeddings on CPU (MPS limitation)...")
            base_model.resize_token_embeddings(len(self.tokenizer))
            base_model.config.pad_token_id = self.tokenizer.pad_token_id
            # Move model to MPS after resize
            base_model = base_model.to(self.device)
            print("Model moved to MPS for inference")
        else:
            base_model.resize_token_embeddings(len(self.tokenizer))
            base_model.config.pad_token_id = self.tokenizer.pad_token_id
        
        # Apply the LoRA adapter if specified, otherwise use base model
        if config.lora_adapter_id:
            print(f"Loading LoRA adapter: {config.lora_adapter_id}")
            self.model = PeftModel.from_pretrained(
                base_model,
                config.lora_adapter_id,
                torch_dtype=dtype,
                device_map="auto",  # Let the system decide device mapping
            )
        else:
            print("Using base model without LoRA adapter")
            self.model = base_model
        
        # Enable gradient checkpointing to save memory
        if hasattr(self.model, "enable_gradient_checkpointing"):
            self.model.enable_gradient_checkpointing()
    
    def _get_device(self) -> torch.device:
        """Returns the device for model execution."""
        return self.device
    
    def _check_system_role_support(self) -> bool:
        """Check if the tokenizer's chat template supports system role."""
        if not hasattr(self.tokenizer, 'chat_template') or self.tokenizer.chat_template is None:
            return False
        
        # Check if template mentions 'system' role - if it does, it supports it
        template_str = str(self.tokenizer.chat_template) if self.tokenizer.chat_template else ""
        # Look for common patterns that indicate system role support
        system_indicators = [
            "messages[0]['role'] == 'system'",
            "'role'] == 'system'",
            "role'] == 'system'",
            "if.*system",
        ]
        
        for pattern in system_indicators:
            if re.search(pattern, template_str, re.IGNORECASE):
                return True
        
        # If no clear indicator, try to test it
        try:
            test_messages = [
                {'role': 'system', 'content': 'test'},
                {'role': 'user', 'content': 'test'}
            ]
            self.tokenizer.apply_chat_template(
                test_messages, 
                tokenize=False, 
                add_generation_prompt=False
            )
            return True
        except Exception:
            return False
        
    def generate_documentation(self, context: List[Dict[str, Any]]) -> Optional[List[Change]]:
        """Generates swagger documentation for the given API contexts."""
        # For large contexts, try processing in batches as fallback
        if len(context) > 5:
            print(f"\nLarge context detected ({len(context)} routes). Trying full context first...")
            result = self._generate_documentation_single(context)
            if result and len(result) == len(context):
                return result
            else:
                print("\nFull context generation incomplete. Falling back to batch processing...")
                return self._generate_documentation_batched(context)
        else:
            return self._generate_documentation_single(context)
    
    def _generate_documentation_single(self, context: List[Dict[str, Any]]) -> Optional[List[Change]]:
        """Generates documentation for all routes in a single pass."""
        system_prompt = self._get_system_prompt()
        user_prompt = self._format_prompt(context)
        
        for attempt in range(self.config.max_retries):
            print(f"\nAttempt {attempt + 1} of {self.config.max_retries}")
            
            try:
                response = self._generate_response(system_prompt, user_prompt)
                changes = self._convert_to_changes(response, context)
                
                if changes is None:
                    print(f"\nInvalid changes format in attempt {attempt + 1} - conversion failed")
                elif len(changes) == 0:
                    print(f"\nInvalid changes format in attempt {attempt + 1} - empty list")
                    changes = None
                else:
                    print(f"\nSuccessfully generated {len(changes)} changes on attempt {attempt + 1}")
                    return changes
                    
            except Exception as e:
                print(f"\nError in attempt {attempt + 1}: {e}")
                if attempt == self.config.max_retries - 1:
                    print("All attempts failed for single-pass generation")
                    return None
                
        return None
    
    def _generate_documentation_batched(self, context: List[Dict[str, Any]], batch_size: int = 3) -> Optional[List[Change]]:
        """Generates documentation by processing routes in smaller batches."""
        print(f"\nProcessing {len(context)} routes in batches of {batch_size}...")
        all_changes = []
        
        for i in range(0, len(context), batch_size):
            batch = context[i:i+batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(context) + batch_size - 1) // batch_size
            
            print(f"\n--- Processing batch {batch_num}/{total_batches} ({len(batch)} routes) ---")
            batch_changes = self._generate_documentation_single(batch)
            
            if batch_changes:
                all_changes.extend(batch_changes)
                print(f"Batch {batch_num} completed: {len(batch_changes)} changes generated")
            else:
                print(f"Batch {batch_num} failed - skipping")
        
        if len(all_changes) == 0:
            print("\nNo changes generated from any batch")
            return None
        
        print(f"\nBatch processing complete: {len(all_changes)} total changes generated (expected {len(context)})")
        return all_changes
        
    def _generate_response(self, system_prompt: str, user_prompt: str) -> List[Dict[str, str]]:
        """Generates a response from the model with timeout support."""
        # Use system role if supported, otherwise combine into user message
        if self.supports_system_role:
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ]
        else:
            # System role not supported, combine into user message
            combined_prompt = f"{system_prompt}\n\n{user_prompt}"
            messages = [
                {'role': 'user', 'content': combined_prompt}
            ]
        
        # Apply chat template with proper attention mask
        inputs = self.tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            return_tensors="pt"
        ).to(self._get_device())
        
        # Create proper attention mask
        attention_mask = torch.ones_like(inputs).to(self._get_device())
        
        # Create a result container and done flag for the thread
        result_container = {"outputs": None, "error": None}
        done_flag = threading.Event()
        timeout_seconds = 2000  # 3 minutes timeout
        
        def generate_with_timeout():
            try:
                print("Attempting generation with reduced parameters...")
                # Reduce max_new_tokens to avoid excessively long generation
                reduced_tokens = min(self.config.max_new_tokens, 2048)
                print(f"Using max_new_tokens={reduced_tokens} (reduced from {self.config.max_new_tokens})")
                
                # Start a progress indicator
                start_time = time.time()
                
                # Add stop sequences to help model stop after JSON
                stop_sequences = ["```", "\n```", "```json", "\n```json"]
                stop_token_ids = []
                for seq in stop_sequences:
                    tokens = self.tokenizer.encode(seq, add_special_tokens=False)
                    if len(tokens) > 0:
                        stop_token_ids.append(tokens[0])  # Use first token of sequence
                
                # First try with deterministic generation (no sampling) and reduced tokens
                result_container["outputs"] = self.model.generate(
                    inputs,
                    attention_mask=attention_mask,
                    max_new_tokens=reduced_tokens,
                    do_sample=False,  # Deterministic generation
                    num_return_sequences=1,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    use_cache=True,
                )
                
                print(f"Generation completed in {time.time() - start_time:.2f} seconds")
                
            except Exception as e:
                result_container["error"] = e
                print(f"Generation failed with error: {e}")
            finally:
                done_flag.set()
        
        # Start generation in a separate thread
        print("Starting generation in background thread...")
        generation_thread = threading.Thread(target=generate_with_timeout)
        generation_thread.daemon = True
        generation_thread.start()
        
        # Monitor progress and check for timeout
        start_time = time.time()
        progress_interval = 10  # seconds
        next_progress = start_time + progress_interval
        
        while not done_flag.is_set():
            time.sleep(1)
            current_time = time.time()
            
            # Print progress updates
            if current_time >= next_progress:
                elapsed = current_time - start_time
                print(f"Still generating... ({elapsed:.0f} seconds elapsed)")
                next_progress = current_time + progress_interval
            
            # Check for timeout
            if current_time - start_time > timeout_seconds:
                print(f"Generation timed out after {timeout_seconds} seconds")
                # We can't actually stop the thread, but we can proceed with a fallback
                break
        
        # Check results
        if not done_flag.is_set() or result_container["error"] is not None:
            # Either timed out or had an error
            error_msg = str(result_container["error"]) if result_container["error"] else "Generation timed out"
            print(f"Using fallback response due to: {error_msg}")
            
            # Create a simple fallback response
            return [{"generated_text": f"""```json
{{
  "changes": [
    {{
      "filepath": "Unable to generate documentation",
      "code": "/**\\n * @swagger\\n * /api/error:\\n *   get:\\n *     description: Error during generation - {error_msg[:100]}\\n */",
      "description": "Generation failed or timed out"
    }}
  ]
}}```"""
            }]
        
        # Process successful generation
        outputs = result_container["outputs"]
        
        try:
            generated_text = self.tokenizer.decode(
                outputs[0][len(inputs[0]):],
                skip_special_tokens=True
            )
            return [{"generated_text": generated_text}]
        except Exception as e:
            print(f"Error decoding generated text: {e}")
            return [{"generated_text": "Error decoding model output"}]
        
    @staticmethod
    def _get_system_prompt() -> str:
        """Returns the system prompt for the model."""
        return """You are an expert in API documentation specializing in JSDoc Swagger comments. Your ONLY task is to GENERATE Swagger documentation, NOT create scripts or tools.

IMPORTANT: 
- DO NOT generate any JavaScript code or scripts
- DO NOT create tools or utilities
- ONLY generate Swagger documentation in the specified JSON format
- ALWAYS quote error descriptions that contain colons to avoid YAML parsing errors
- For error descriptions like "error: Not found", wrap them in single quotes like 'error: Not found'
- STOP immediately after the closing }} of the JSON object - do not generate anything else
- Generate EXACTLY the number of changes specified in the task (one per API route)

Your output MUST be a single JSON object containing Swagger documentation comments like this:

```json
{{
  "changes": [
    {{
      "filepath": "<FILEPATH>",
      "code": "/**\\n * @swagger\\n * /api/users:\\n *   post:\\n *     tags:\\n *       - Users\\n *     summary: Create user\\n *     requestBody:\\n *       required: true\\n *       content:\\n *         application/json:\\n *           schema:\\n *             type: object\\n *             properties:\\n *               name:\\n *                 type: string\\n *     responses:\\n *       201:\\n *         description: Created\\n *       400:\\n *         description: 'Bad request: Invalid input'\\n */",
      "description": "Documentation for create user endpoint"
    }}
  ]
}}
```

CRITICAL RULES:
1. Generate exactly ONE change entry for EACH API route provided in the context
2. The "filepath" field MUST match the "filename" from the "codeContext" of each route (e.g., "src/app.js", not "/api/users")
3. Stop immediately after the closing }} - do not generate any text after the JSON
4. Process routes in the exact order they appear in the context array"""


    @staticmethod
    def _format_prompt(context: List[Dict[str, Any]]) -> str:
        """Formats the user prompt with the given context."""
        num_routes = len(context)
        return f"""TASK: Generate Swagger documentation comments for {num_routes} API routes.

REQUIREMENTS:
- Generate EXACTLY {num_routes} changes (one for each route in order)
- Each change must correspond to one API route in the context below, in the SAME ORDER
- The "filepath" in each change MUST be the "filename" from that route's "codeContext" (e.g., "src/app.js")
- Stop immediately after the closing }} of the JSON object
- Do not generate any text after the JSON

DO NOT:
❌ Create JavaScript scripts or tools
❌ Write code to extract comments
❌ Generate anything other than Swagger documentation
❌ Skip any routes - you must generate documentation for ALL {num_routes} routes
❌ Use API paths as filepaths - use the actual filename from codeContext

DO:
✅ Generate a single JSON object with Swagger documentation
✅ Generate exactly {num_routes} entries in the "changes" array (one per route)
✅ Use codeContext.filename as the filepath for each change
✅ Process routes in the exact order they appear in the context array
✅ Follow the exact format shown in the system prompt
✅ Include all required Swagger elements (path, method, tags, etc.)
✅ Stop immediately after the closing }}

API Context ({num_routes} routes):
{json.dumps(context, indent=2)}"""

    def _extract_json_from_text(self, text: str) -> Optional[str]:
        """Extracts complete JSON object from text, handling cases where model continues generating."""
        # First, try to find JSON in code blocks
        start_marker = "```json"
        json_start_idx = text.find(start_marker)
        
        if json_start_idx == -1:
            start_marker = "```"
            json_start_idx = text.find(start_marker)
        
        if json_start_idx != -1:
            # Find the opening brace after the marker
            brace_start = text.find('{', json_start_idx)
            if brace_start == -1:
                # Try without code blocks
                brace_start = text.find('{')
                if brace_start == -1:
                    return None
        else:
            # No code blocks, look for opening brace
            brace_start = text.find('{')
            if brace_start == -1:
                return None
        
        # Find the matching closing brace by counting braces
        brace_count = 0
        i = brace_start
        while i < len(text):
            if text[i] == '{':
                brace_count += 1
            elif text[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    # Found the complete JSON object
                    json_text = text[brace_start:i+1]
                    return json_text
            i += 1
        
        # If we didn't find a complete JSON, try to extract what we have
        # and see if it's valid JSON (might be incomplete)
        potential_json = text[brace_start:]
        return potential_json
    
    def _convert_to_changes(self, response: List[Dict[str, str]], context: List[Dict[str, Any]]) -> Optional[List[Change]]:
        """Converts the model response to a list of changes."""
        try:
            text = response[0]['generated_text']
            
            print("\nDebug - Full response text (first 500 chars):")
            print(text[:500])
            if len(text) > 500:
                print(f"... (truncated, total length: {len(text)} chars)")
            
            # Extract JSON using improved method
            json_text = self._extract_json_from_text(text)
            
            if json_text is None:
                raise ValueError("No JSON found in response")
            
            print("\nDebug - Extracted JSON text:")
            print(json_text[:1000] if len(json_text) > 1000 else json_text)
            if len(json_text) > 1000:
                print(f"... (truncated, total length: {len(json_text)} chars)")
            
            # Parse JSON
            json_data = json.loads(json_text)
            
            # Validate that we have the expected number of changes
            num_changes = len(json_data['changes'])
            num_context = len(context)
            
            if num_changes != num_context:
                print(f"\nWarning: Number of changes ({num_changes}) does not match context length ({num_context})")
                if num_changes < num_context:
                    print(f"Model only generated {num_changes} out of {num_context} expected changes. This may be a model limitation.")
                    # We'll still try to process what we have, matching by index
                else:
                    print(f"Model generated {num_changes} changes but only {num_context} were expected. Using first {num_context}.")
                    json_data['changes'] = json_data['changes'][:num_context]
            
            # Keep track of line offsets for each file
            file_offsets = {}  # "filepath (str): offset (int)"
            
            # Create a mapping of context entries by filename for better matching
            context_by_filename = {}
            for i, ctx in enumerate(context):
                filename = ctx['codeContext']['filename']
                if filename not in context_by_filename:
                    context_by_filename[filename] = []
                context_by_filename[filename].append((i, ctx))
            
            # Process each change to add line numbers
            processed_changes = []
            used_context_indices = set()
            
            for change_idx, change_data in enumerate(json_data['changes']):
                matching_context = None
                context_idx = None
                
                # Try to match by filepath first
                generated_filepath = change_data.get('filepath', '')
                
                # First, try exact filename match
                if generated_filepath in context_by_filename:
                    # Use the first unused context entry for this filename
                    for idx, ctx in context_by_filename[generated_filepath]:
                        if idx not in used_context_indices:
                            matching_context = ctx
                            context_idx = idx
                            used_context_indices.add(idx)
                            break
                
                # If no match by filename, try by index (fallback)
                if matching_context is None and change_idx < len(context):
                    if change_idx not in used_context_indices:
                        matching_context = context[change_idx]
                        context_idx = change_idx
                        used_context_indices.add(change_idx)
                        print(f"\nWarning: Matched change {change_idx} by index (filepath '{generated_filepath}' didn't match)")
                
                # If still no match, skip this change
                if matching_context is None:
                    print(f"\nWarning: Could not match change {change_idx} with filepath '{generated_filepath}' to any context entry. Skipping.")
                    continue
                
                # Use the correct filepath from context
                filepath = matching_context['codeContext']['filename']
                
                # Get current offset for this file
                current_offset = file_offsets.get(filepath, 0)
                
                # Get the original line where we want to insert
                original_line = matching_context['codeContext']['line']['beginning']
                
                # Calculate start_line with current offset
                start_line = original_line + current_offset - 1
                
                # Calculate number of lines in the new code
                code_lines = change_data['code'].count('\n') + 1
                
                # Create Change object
                change = Change(
                    start_line=start_line,
                    filepath=filepath,
                    code=change_data['code'],
                    description=change_data['description']
                )
                processed_changes.append(change)
                
                # Update the offset for this file
                file_offsets[filepath] = current_offset + code_lines
            
            # Check if we got any valid changes
            if len(processed_changes) == 0:
                print("\nError: No valid changes could be matched to context entries")
                return None
            
            if len(processed_changes) < num_context:
                print(f"\nWarning: Only processed {len(processed_changes)} out of {num_context} expected changes")
                # Still return what we have - partial results are better than nothing
            
            return processed_changes
            
        except Exception as e:
            print(f"\nError extracting JSON from response: {e}")
            if 'text' in locals():
                print("\nRaw text that caused the error:")
                print(text)
            return None