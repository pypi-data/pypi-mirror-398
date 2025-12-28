import numpy as np
import json
import re
import pickle
class FastKernelRouter:
    def __init__(self, token_set, prefix_set):
        self.tags = [t.lower() for t in token_set]
        self.prefixes = [k.lower() for k in prefix_set]
        
        # Semantic mapping: (Tokens x Keys)
        self.W_semantic = np.random.randn(len(self.tags), len(self.prefixes)) * 0.05
        
        # Kernel: Pos_Val, Pos_Key, Pos_Aux, Dist(Val, Key)
        # Added distance as a feature to improve precision
        self.W_kernel = np.random.randn(4, 1) * 0.05
        self.b_kernel = 0.0
        
        self.W_tagsize = np.random.randn(4, 1) * 0.05
        self.b_tagsize = 0.0

    def _get_pos(self, sentence, target):
        try:
            idx = sentence.lower().find(target.lower())
            return idx / len(sentence) if idx != -1 else -1.0
        except:
            print("error") 
            return -1.0

    def _extract_aux(self, sentence):
        words = re.findall(r'\w+', sentence.lower())
        # Aux tokens are words not in our set or keys
        aux_positions = [i/len(words) for i, w in enumerate(words) 
                         if w not in self.tags and w not in self.prefixes]
        return np.mean(aux_positions) if aux_positions else 0.5

    def _sigmoid(self, x):
        return 1 / (1 + np.exp(-np.clip(x, -15, 15)))
    
    def forward(self, feat, v_idx, k_idx):
        score = np.dot(self.W_kernel.T, feat) + self.W_semantic[v_idx, k_idx] + self.b_kernel
        prob = self._sigmoid(score)[0,0]
        return prob
    
    def train(self, training_data, epochs=1000, lr=0.1):
        # Weight decay to keep loss from exploding
        decay = 0.999 
        
        for epoch in range(epochs):
            total_loss = 0
            
            for sentence, target_dict in training_data:
                sentence = sentence.lower()
                pos_prefix = np.array([self._get_pos(sentence, k) for k in self.prefixes])
                pos_tag = np.array([self._get_pos(sentence, v) for v in self.tags])
                pos_aux = self._extract_aux(sentence)

                for k_idx, key in enumerate(self.prefixes):
                    # 1. Identify Target
                    actual_val = target_dict.get(key)
                    y_true = np.zeros(len(self.tags))
                    if actual_val:
                        target_list = [actual_val] if isinstance(actual_val, str) else actual_val
                        for av in target_list:
                            if av.lower() in self.tags:
                                y_true[self.tags.index(av.lower())] = 1

                    # 2. Forward & Update for each token present
                    present_indices = np.where(pos_tag != -1.0)[0]
                    for v_idx in present_indices:
                        dist = abs(pos_tag[v_idx] - pos_prefix[k_idx])
                        # Feature Vector: [ValPos, KeyPos, AuxPos, Distance]
                        feat = np.array([[pos_tag[v_idx]], [pos_prefix[k_idx]], [pos_aux], [dist]])
                        
                        # Forward
                        prob = self.forward(feat, v_idx, k_idx)
                        
                        # Log Loss calculation
                        eps = 1e-15
                        total_loss -= (y_true[v_idx] * np.log(prob + eps) + (1 - y_true[v_idx]) * np.log(1 - prob + eps))

                        # Backprop (Gradients)
                        error = prob - y_true[v_idx]
                        
                        # Update Kernel Weights
                        self.W_kernel -= lr * error * feat
                        self.b_kernel -= lr * error
                        
                        # Update Semantic Weights
                        self.W_semantic[v_idx, k_idx] -= lr * error

            # Learning Rate Decay
            lr *= decay
            
            if epoch % 100 == 0:
                avg_loss = total_loss / (len(training_data) * len(self.prefixes))
                print(f"Epoch {epoch:4d} | Avg Log-Loss: {avg_loss:.6f}")

    def predict(self, sentence, template = {}):
        
        sentence = sentence.lower()
        pos_prefix = np.array([self._get_pos(sentence, k) for k in self.prefixes])
        pos_tag = np.array([self._get_pos(sentence, v) for v in self.tags])
        pos_aux = self._extract_aux(sentence)
        present_indices = np.where(pos_tag != -1.0)[0]
        prob_matrix = np.zeros((len(self.prefixes), len(present_indices)))
        # print(pos_tag, sentence, "\n", self.tags)
        result = {k: None for k in self.prefixes}
        
        for k_idx, key in enumerate(self.prefixes):
            best_prob = -1
            best_token = None
            
            for v_idx in present_indices:
                dist = abs(pos_tag[v_idx] - pos_prefix[k_idx])
                feat = np.array([[pos_tag[v_idx]], [pos_prefix[k_idx]], [pos_aux], [dist]])
                
                prob = self.forward(feat, v_idx, k_idx)
                # prob_matrix[k_idx, v_idx] = prob
                if prob > best_prob:
                    best_prob = prob
                    best_token = self.tags[v_idx]
            
            # Use threshold to decide if we keep the best token
            if best_prob > 0.7:
                result[key] = best_token
        # print(prob_matrix)
        return result
# --- Setup Data ---

if __name__ == "__main__":
    token_set = ["traction", "bead image previous", "bead image next", "displacement", "bead image", "from", "the", "with", "as", "and", "provided", "uploaded"]
    prefix_set = ["image", "array", "calculate"]
    # aux_tokens = ["from", "the", "with", "as", "and", "provided", "uploaded"]

    # Example Training Dataset
    training_data = []
    with open("s2qdata/training_set.json", "r") as f:
        data = json.load(f)
        for entry in data:
            training_data.append((
                entry["input"],
                entry["output"]
            ))

    # --- Execution ---

    model = FastKernelRouter(token_set, prefix_set)
    model.train(training_data, epochs=5000)

    # Save (Serialize) to a file
    with open('s2qmodel.pkl', 'wb') as file:
        pickle.dump(model, file)

    # Test the model
    with open("s2qdata/test_set.json", "r") as f:
        data = json.load(f)
        for entry in data:
            test_input = entry["input"]
            output_query = model.predict(test_input)
            print("\nInput Sentence:", test_input)
            print("Predict Query:", output_query)
            print("Actual  Query:", entry["output"])