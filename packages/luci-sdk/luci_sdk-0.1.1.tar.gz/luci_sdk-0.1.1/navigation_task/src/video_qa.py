"""
Video Question Answering for Egocentric Navigation
Based on Ego-ST benchmark patterns
"""

import json
import re
import torch
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info


class NavigationVideoQA:
    """Video QA system for egocentric navigation analysis"""

    def __init__(self, model_path="ST-R1-mcq"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.processor = None
        self._load_model(model_path)

    def _load_model(self, model_path):
        """Load model with fallback to base model"""
        try:
            self.model = Qwen2VLForConditionalGeneration.from_pretrained(
                model_path, dtype=torch.bfloat16, device_map=self.device
            )
            self.processor = AutoProcessor.from_pretrained(model_path)
        except Exception:
            # Fallback to base model
            model_path = "Qwen/Qwen2-VL-2B-Instruct"
            self.model = Qwen2VLForConditionalGeneration.from_pretrained(
                model_path, dtype=torch.bfloat16, device_map=self.device
            )
            self.processor = AutoProcessor.from_pretrained(model_path)

    def ask_question(self, video_path, question, options=None):
        """Ask question about video (MCQ or open-ended)"""
        if options:
            return self._ask_mcq(video_path, question, options)
        return self._ask_open(video_path, question)

    def _ask_mcq(self, video_path, question, options):
        """Multiple choice question"""
        options_str = "\n".join([f"{chr(65+i)}. {opt}" for i, opt in enumerate(options)])
        prompt = f"{question}\n\nOptions:\n{options_str}\n\nAnswer with letter only (A-D):"

        messages = [{
            "role": "user",
            "content": [
                {"type": "video", "video": video_path, "max_pixels": 360*420, "fps": 1.0},
                {"type": "text", "text": prompt}
            ]
        }]

        response = self._generate_response(messages)
        choice = self._extract_choice(response)

        return {
            "question": question,
            "options": options,
            "answer": choice,
            "selected_option": options[ord(choice) - ord('A')] if choice in 'ABCD' else None
        }

    def _ask_open(self, video_path, question):
        """Open-ended question"""
        messages = [{
            "role": "user",
            "content": [
                {"type": "video", "video": video_path, "max_pixels": 360*420, "fps": 1.0},
                {"type": "text", "text": question}
            ]
        }]

        response = self._generate_response(messages)
        return {"question": question, "answer": response}

    def _generate_response(self, messages):
        """Generate model response"""
        text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        image_inputs, video_inputs, video_kwargs = process_vision_info(messages, return_video_kwargs=True)

        inputs = self.processor(
            text=[text], images=image_inputs, videos=video_inputs,
            padding=True, return_tensors="pt", **video_kwargs
        ).to(self.device)

        generated_ids = self.model.generate(**inputs, max_new_tokens=512)
        generated_ids_trimmed = [
            out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]

        output = self.processor.batch_decode(
            generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )
        return output[0] if output else ""

    def _extract_choice(self, response):
        """Extract A-D choice from response"""
        response = response.strip()
        match = re.match(r'^([A-D])\b', response)
        if match:
            return match.group(1)
        for char in response:
            if char in 'ABCD':
                return char
        return 'A'  # Default fallback