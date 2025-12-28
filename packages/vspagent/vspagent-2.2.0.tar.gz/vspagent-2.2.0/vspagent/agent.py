"""VSP Agent - Core functionality"""

from typing import List, Optional

# Biodata
biodata = {
    "name": "VSP Agent",
    "creator": "Vishnu Suresh Perumbavoor",
    "founder_of": ["VSP Enterprises", "VSP Intelligence"],
    "created_on": "28 April 2023",
    "marital_status": "Single (Not married)",
    "political_affiliation": "None",
    "education": "Not a graduate (No degree)",
    "roles": ["SWE", "Singer", "YouTuber"],
    "interests": ["startups", "engineering", "geopolitics", "history"],
    "corporate": ["Trenser"],
    "technologies": [
        "React", "Node.js", "FastAPI", "Express", "MongoDB", 
        "Docker", "OHIF", "Cornerstone3D", "VTKjs", "DICOM"
    ],
    "accomplishments": [
        "Won 3rd prize in Vaiga Agrihack 2023",
        "Participated in Rajasthan IT Hackathon 2023",
        "Won 1st prize in startup idea presentation at Palakkad"
    ],
    "socials": {
        "linkedin": "https://www.linkedin.com/in/vishnu-suresh-perumbavoor/",
        "twitter": "https://twitter.com/vspeeeeee",
        "github": "https://github.com/vishnusureshperumbavoor",
        "youtube": "https://www.youtube.com/@vishnusureshperumbavoor9721/videos",
        "instagram": "https://www.instagram.com/vishnusureshperumbavoor/",
    }
}


class VSPAgent:
    """AI-powered agent for VSP information"""
    
    def __init__(self):
        self.biodata = biodata
        self.model = None
        self.tokenizer = None
    
    def init_ai(self):
        """Initialize AI model (Qwen2.5-0.5B)"""
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            import torch
            
            print("🚀 Initializing VSP Agent...")
            print("   🧠 Loading AI brain with Qwen2.5-0.5B...")
            
            model_name = "Qwen/Qwen2.5-0.5B-Instruct"
            
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            
            # Load model with GPU optimization
            if torch.cuda.is_available():
                # GPU: Use FP16 for 2x faster inference
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    torch_dtype=torch.float16
                ).cuda()
                device_info = f"GPU (CUDA) - FP16 Optimized"
            else:
                # CPU: Use default precision
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    torch_dtype=torch.float32
                )
                device_info = "CPU"
            
            print("✅ VSP Agent is ready!")
            print(f"   🤖 Device: {device_info}")
            
        except Exception as e:
            print(f"❌ Error initializing AI: {e}")
            print("💡 Install required packages: pip install transformers torch")
    
    def chat(self, message: str, conversation_history: Optional[List] = None) -> str:
        """Chat with the AI agent"""
        if self.model is None:
            return "Please initialize AI first using init_ai()"
        
        system_context = f"""You are an AI assistant answering questions about Vishnu Suresh Perumbavoor (VSP).

Key Facts:
- Name: {self.biodata['creator']}
- Marital Status: {self.biodata['marital_status']}
- Education: {self.biodata['education']}
- Founder: {', '.join(self.biodata['founder_of'])} (founded {self.biodata['created_on']})
- Works at: {', '.join(self.biodata['corporate'])}
- Roles: {', '.join(self.biodata['roles'])}
- Tech Stack: {', '.join(self.biodata['technologies'][:6])}
- Interests: {', '.join(self.biodata['interests'])}
- Achievements: 3rd prize Vaiga Agrihack 2023, 1st prize startup presentation Palakkad
- Social: LinkedIn, GitHub, YouTube, Twitter, Instagram

Answer concisely and naturally using "he/his" (third person). Only use facts above."""

        messages = [{"role": "system", "content": system_context}]
        
        if conversation_history:
            messages.extend(conversation_history)
        
        messages.append({"role": "user", "content": message})
        
        try:
            # Generate response
            inputs = self.tokenizer.apply_chat_template(
                messages, 
                return_tensors="pt",
                add_generation_prompt=True
            ).to(self.model.device)
            
            outputs = self.model.generate(
                inputs,
                max_new_tokens=256,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            # Decode only the new tokens (not the input)
            generated_ids = outputs[0][inputs.shape[1]:]
            response = self.tokenizer.decode(generated_ids, skip_special_tokens=True).strip()
            
            return response
            
        except Exception as e:
            return f"Error generating response: {e}"
    

