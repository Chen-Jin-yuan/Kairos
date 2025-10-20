from transformers import AutoTokenizer
import csv


class TokenCounter:
    def __init__(self, agents_use_model):
        self.tokenizer_map = {}
        self.agents_use_model = agents_use_model
        self.output_file = "./data/tokens.csv"

        for agent_name, model in agents_use_model.items():
            if model not in self.tokenizer_map:
                tokenizer = AutoTokenizer.from_pretrained(model)
                self.tokenizer_map[model] = tokenizer

        with open(self.output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['msg_id', 'agent_name', 'prompt_len', 'all_text_len', 'generate_text_len']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

    def count_tokens(self, agent_name, text):
        model = self.agents_use_model[agent_name]
        tokenizer = self.tokenizer_map[model]
        tokens = tokenizer.tokenize(text)
        token_count = len(tokens)
        return token_count

    def save_token_info(self):
        # save execution info
        pass