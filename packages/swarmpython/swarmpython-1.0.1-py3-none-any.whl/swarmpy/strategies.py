import numpy as np
import math
from collections import Counter

# --- 1. NUMERIC STRATEGY (For Regression/Numbers) ---
class NumericalStrategy:
    def __init__(self, sensitivity=1.5):
        self.sensitivity = sensitivity

    def aggregate(self, values: list, priorities: list = None):
        """
        Aggregates numeric predictions using Z-Score outlier removal 
        and weighted averaging.
        """
        # 1. Sanitize Data
        clean_values = []
        clean_weights = []
        
        for i, val in enumerate(values):
            if val is not None and isinstance(val, (int, float)) and not np.isnan(val):
                w = priorities[i] if (priorities and i < len(priorities)) else 1.0
                clean_values.append(val)
                clean_weights.append(w)
        
        if not clean_values:
            return {"final_output": None, "analytics": {"error": "No valid numeric outputs"}}

        data_arr = np.array(clean_values)
        weight_arr = np.array(clean_weights)

        # 2. Outlier Removal (Z-Score)
        if len(data_arr) > 2 and np.std(data_arr) > 0:
            mean = np.mean(data_arr)
            std = np.std(data_arr)
            z_scores = np.abs((data_arr - mean) / std)
            mask = z_scores < self.sensitivity
            
            # Apply filter
            filtered_data = data_arr[mask]
            filtered_weights = weight_arr[mask]

            if len(filtered_data) == 0: 
                # If too strict, revert to raw
                filtered_data = data_arr
                filtered_weights = weight_arr
        else:
            filtered_data = data_arr
            filtered_weights = weight_arr

        # 3. Weighted Average
        weighted_sum = np.sum(filtered_data * filtered_weights)
        total_weight = np.sum(filtered_weights)
        final_output = weighted_sum / total_weight if total_weight > 0 else 0

        return {
            "final_output": float(final_output),
            "analytics": {
                "raw_inputs": data_arr.tolist(),
                "filtered_inputs": filtered_data.tolist(),
                "std_dev": float(np.std(filtered_data)),
                "min": float(np.min(filtered_data)),
                "max": float(np.max(filtered_data))
            }
        }


# --- 2. VOTING STRATEGY (For Text/Classification/Images) ---
class VotingStrategy:
    def aggregate(self, values: list, priorities: list = None):
        """
        Aggregates labels using Weighted Majority Voting 
        and calculates Confidence & Entropy (Confusion).
        """
        # 1. Sanitize Data
        clean_votes = []
        clean_weights = []
        
        for i, val in enumerate(values):
            if val is not None:
                # Convert everything to string for voting
                clean_votes.append(str(val))
                w = priorities[i] if (priorities and i < len(priorities)) else 1.0
                clean_weights.append(w)
        
        if not clean_votes:
            return {"final_output": None, "analytics": {"error": "No valid votes"}}

        # 2. Weighted Tally
        vote_tally = {}
        total_weight = 0.0
        
        for label, weight in zip(clean_votes, clean_weights):
            vote_tally[label] = vote_tally.get(label, 0) + weight
            total_weight += weight

        # 3. Find Winner
        sorted_votes = sorted(vote_tally.items(), key=lambda item: item[1], reverse=True)
        winner = sorted_votes[0][0]
        winner_score = sorted_votes[0][1]

        # --- 4. ANALYTICS ENGINE (The "Text Stuff") ---
        
        # A. Confidence (0.0 to 1.0)
        confidence = winner_score / total_weight if total_weight > 0 else 0.0

        # B. Entropy (Confusion Metric)
        # 0.0 = Perfect Agreement
        # High Score = High Confusion
        entropy = 0.0
        for label, score in vote_tally.items():
            prob = score / total_weight
            if prob > 0:
                entropy -= prob * math.log2(prob)

        # C. Human-Readable Agreement Level
        if confidence == 1.0:
            agreement = "Unanimous"
        elif confidence > 0.75:
            agreement = "Strong Consensus"
        elif confidence > 0.5:
            agreement = "Majority"
        else:
            agreement = "High Contention (Uncertain)"

        return {
            "final_output": winner,
            "analytics": {
                "winner_confidence": round(confidence, 4),
                "swarm_entropy": round(entropy, 4),
                "agreement_level": agreement,
                "vote_distribution": vote_tally,
                "total_votes": len(clean_votes)
            }
        }