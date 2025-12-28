import numpy as np
import json 
import pickle
from importlib import resources
class ContextSequenceLearner:
    def __init__(self, graph, all_tokens):
        self.graph = graph
        self.tokens = sorted(list(all_tokens))
        self.token_to_idx = {t: i for i, t in enumerate(self.tokens)}
        self.idx_to_token = {i: t for i, t in enumerate(self.tokens)}
        
        # Dimensions
        self.vocab_size = len(self.tokens)
        # Weight Matrix: maps context+current_state to next_state
        # We use (vocab_size * 2) because: [Context Vector ; Current State Vector]
        self.W = np.random.randn(self.vocab_size, self.vocab_size * 2) * 0.1
        self.b = np.zeros((self.vocab_size, 1))

    def _get_context_vector(self, T):
        """Recursively flattens tree T into a multi-hot vector."""
        vec = np.zeros((self.vocab_size, 1))
        def traverse(node):
            if isinstance(node, dict):
                for k, v in node.items():
                    if k in self.token_to_idx: vec[self.token_to_idx[k]] = 1
                    traverse(v)
            elif isinstance(node, str):
                if node in self.token_to_idx: vec[self.token_to_idx[node]] = 1
        traverse(T)
        return vec

    def softmax(self, x):
        e_x = np.exp(x - np.max(x))
        return e_x / e_x.sum(axis=0)

    def predict(self, T):
        """Op(G, T) -> S. T is the only input."""
        context_vec = self._get_context_vector(T)
        
        # 1. Predict Start Node
        # Input for start is [Context ; Zeros] because there is no 'previous' state
        start_input = np.vstack((context_vec, np.zeros((self.vocab_size, 1))))
        start_logits = np.dot(self.W, start_input) + self.b
        
        # Filter: Start node must be a key in our graph G
        start_mask = np.zeros((self.vocab_size, 1))
        for node in self.graph.keys():
            start_mask[self.token_to_idx[node]] = 1
        
        start_probs = self.softmax(start_logits) * start_mask
        current_node = self.idx_to_token[np.argmax(start_probs)]
        
        sequence = [current_node]
        
        # 2. Predict Traversal
        for _ in range(10): # Safety limit
            curr_idx = self.token_to_idx[current_node]
            state_vec = np.zeros((self.vocab_size, 1))
            state_vec[curr_idx] = 1
            
            combined_input = np.vstack((context_vec, state_vec))
            logits = np.dot(self.W, combined_input) + self.b
            probs = self.softmax(logits)
            
            # Mask based on Graph G allowed transitions
            neighbors = self.graph.get(current_node, [])
            if not neighbors: break # Reached a leaf node
            
            mask = np.zeros((self.vocab_size, 1))
            for n in neighbors: mask[self.token_to_idx[n]] = 1
            
            masked_probs = probs * mask
            if np.sum(masked_probs) == 0: break
            
            current_node = self.idx_to_token[np.argmax(masked_probs)]
            sequence.append(current_node)
            
        return sequence

    def train(self, training_pairs, epochs=200, lr=0.05):
        for epoch in range(epochs):
            loss = 0
            for T, target_S in training_pairs:
                context_vec = self._get_context_vector(T)
                
                # We train every transition in the sequence including the start
                # Step 0: Context -> S[0]
                # Step 1: Context + S[0] -> S[1] ...
                for i in range(len(target_S)):
                    if i == 0:
                        prev_state = np.zeros((self.vocab_size, 1))
                    else:
                        prev_state = np.zeros((self.vocab_size, 1))
                        prev_state[self.token_to_idx[target_S[i-1]]] = 1
                    
                    x = np.vstack((context_vec, prev_state))
                    target_idx = self.token_to_idx[target_S[i]]
                    
                    # Forward
                    probs = self.softmax(np.dot(self.W, x) + self.b)
                    
                    # Backprop
                    y_true = np.zeros((self.vocab_size, 1))
                    y_true[target_idx] = 1
                    error = probs - y_true
                    
                    self.W -= lr * np.dot(error, x.T)
                    self.b -= lr * error
                    loss += -np.log(probs[target_idx] + 1e-9)
            
            if epoch % 50 == 0: print(f"Epoch {epoch}, Loss: {loss[0]:.4f}")
# --- Execution ---
if __name__ == "__main__":
    G = {
        "image process displacement": ["calculate displacement"],
        "image process beads": ["calculate displacement"],
        "calculate displacement": ["calculate traction"]
    }

    # All unique tokens in the system
    tokens = {"image", "calculate displacement", "query", "traction", 
            "image process displacement", "image process beads", "calculate traction"}

    # Example Training Data (Tree T, Sequence S)
    train_set = []
    with open("q2sdata/training_set.json",  "r") as f:
        data = json.load(f)
        for entry in data:
            train_set.append((
                entry["input"],
                entry["output"]
            ))


    model = ContextSequenceLearner(G, tokens)
    model.train(train_set, epochs=1000)

    # Save (Serialize) to a file
    with open('q2smodel.pkl', 'wb') as file:
        pickle.dump(model, file)

    # Prediction
    with open("q2sdata/test_set.json", "r") as f:
        data = json.load(f)
        for entry in data:
            T_query = entry["input"]
            predicted_sequence = model.predict(T_query)
            print(f"\nInput query: {T_query}")
            print(f"Predict Seq: {predicted_sequence}")
            print(f"Actual  Seq: {entry["output"]}")