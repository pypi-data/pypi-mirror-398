import os
import re
import numpy as np
import joblib
import xgboost as xgb


LAG = 10
W = 0.05
AA20 = "ACDEFGHIKLMNPQRSTVWY"

HYDRO = {'A':1.8,'C':2.5,'D':-3.5,'E':-3.5,'F':2.8,'G':-0.4,'H':-3.2,'I':4.5,'K':-3.9,'L':3.8,'M':1.9,'N':-3.5,'P':-1.6,'Q':-3.5,'R':-4.5,'S':-0.8,'T':-0.7,'V':4.2,'W':-0.9,'Y':-1.3}
POLAR = {'A':8.1,'C':5.5,'D':13.0,'E':12.3,'F':5.2,'G':9.0,'H':10.4,'I':5.2,'K':11.3,'L':4.9,'M':5.7,'N':11.6,'P':8.0,'Q':10.5,'R':10.5,'S':9.2,'T':8.6,'V':5.9,'W':5.4,'Y':6.2}
CHARGE = {'A':0,'C':0,'D':-1,'E':-1,'F':0,'G':0,'H':0.5,'I':0,'K':1,'L':0,'M':0,'N':0,'P':0,'Q':0,'R':1,'S':0,'T':0,'V':0,'W':0,'Y':0}
PROPERTIES = {"hydro": HYDRO, "polar": POLAR, "charge": CHARGE}

CTD_GROUPS = {
    "hydrophobicity": [set("RKEDQN"), set("GASTPHY"), set("CLVIMFW")],
    "normalized_vdw": [set("GASTPD"), set("NVEQIL"), set("MHKFRYW")],
    "polarizability": [set("GASDT"), set("CPNVEQIL"), set("KMHFRYW")],
    "secondary":      [set("NDEQST"), set("AILMV"), set("CFGHKPRYW")],
    "solvent_access": [set("ALFCGIVW"), set("RKQEND"), set("MPSTHY")],
    "polarity":       [set("LIFWCMVY"), set("PATGS"), set("HQRKNED")],
    "charge":         [set("KR"), set("ANCQGHILMFPSTWYV"), set("DE")]
}


def pse_aac_multi(seq, lam=LAG, w=W, props=PROPERTIES, add_len=True):

    seq = re.sub("[^ACDEFGHIKLMNPQRSTVWY]", "", seq.upper())
    L = len(seq)
    if L == 0:
        base_feat = np.zeros(20 + lam * len(props), dtype=float)
        return np.concatenate([base_feat, [0]]) if add_len else base_feat
    aac = np.array([seq.count(aa) / L for aa in AA20], dtype=float)
    thetas = []
    for pname, prop in props.items():
        theta = np.zeros(lam, dtype=float)
        for k in range(1, lam + 1):
            if L <= k: break
            diffs = [(prop[seq[i]] - prop[seq[i+k]]) ** 2 for i in range(L - k)]
            theta[k-1] = np.mean(diffs)
        thetas.append(theta)
    thetas = np.concatenate(thetas)
    denom = 1.0 + w * thetas.sum()
    feat = np.concatenate([aac, w * thetas]) / denom
    if add_len: feat = np.concatenate([feat, [L]])
    return feat

def ctd_features(seq):

    seq = re.sub("[^ACDEFGHIKLMNPQRSTVWY]", "", seq.upper())
    L = len(seq)
    if L == 0: return np.zeros(len(CTD_GROUPS) * 21, dtype=float)
    all_feats = []
    for pname, groups in CTD_GROUPS.items():
        gseq = []
        for aa in seq:
            if aa in groups[0]: gseq.append(1)
            elif aa in groups[1]: gseq.append(2)
            elif aa in groups[2]: gseq.append(3)
            else: gseq.append(0)
        gseq = np.array(gseq)
        comp = [np.sum(gseq == g) / L for g in [1,2,3]]
        trans = []
        for g1 in [1,2,3]:
            for g2 in [1,2,3]:
                if g1 < g2:
                    cnt = np.sum((gseq[:-1]==g1)&(gseq[1:]==g2)) + np.sum((gseq[:-1]==g2)&(gseq[1:]==g1))
                    trans.append(cnt / (L-1))
        dist = []
        for g in [1,2,3]:
            idx = np.where(gseq == g)[0]
            if len(idx) == 0: dist.extend([0,0,0,0,0])
            else: dist.extend([idx[0]/L, idx[int(0.25*len(idx))]/L, idx[int(0.50*len(idx))]/L, idx[int(0.75*len(idx))]/L, idx[-1]/L])
        all_feats.extend(comp+trans+dist)
    return np.array(all_feats, dtype=float)

def window_aac(seq, n_segments=3):

    seq = re.sub("[^ACDEFGHIKLMNPQRSTVWY]", "", seq.upper())
    L = len(seq)
    if L == 0: return np.zeros(n_segments * 20, dtype=float)
    seg_size = max(1, L // n_segments)
    feats = []
    for i in range(n_segments):
        start = i * seg_size
        end = L if i == n_segments-1 else (i+1)*seg_size
        sub = seq[start:end]
        if len(sub) == 0: feats.extend([0]*20)
        else: feats.extend([sub.count(aa)/len(sub) for aa in AA20])
    return np.array(feats, dtype=float)

def extract_features(seq):

    pse = pse_aac_multi(seq, props=PROPERTIES)
    ctd = ctd_features(seq)
    win = window_aac(seq, n_segments=3)
    return np.concatenate([pse, ctd, win])


class RAEP:
    def __init__(self):
  
        curr_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(curr_dir, "enzyme_xgb_model.pkl")
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at {model_path}. Please check installation.")
            
        print(f"Loading RAEP model from: {model_path}")
        self.model = joblib.load(model_path)

    def predict(self, sequence):
        """
        Return: 0 (Non-Enzyme) or 1 (Enzyme)
        """

        feats = extract_features(sequence)
  
        feats_reshaped = feats.reshape(1, -1)

        pred = self.model.predict(feats_reshaped)[0]
        return int(pred)

    def predict_proba(self, sequence):
        """
        Return: float (0.0 ~ 1.0)
        """
        feats = extract_features(sequence)
        feats_reshaped = feats.reshape(1, -1)
        prob = self.model.predict_proba(feats_reshaped)[0][1]
        return float(prob)
    
    def read_fasta(self, fasta_file):
        """
        
        Args:
            fasta_file: str
            
        Returns:
            dict: {seq_id: sequence}
        """
        sequences = {}
        current_id = None
        current_seq = []
        
        with open(fasta_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('>'):
                    if current_id is not None:
                        sequences[current_id] = ''.join(current_seq)
                    current_id = line[1:].split()[0]  
                    current_seq = []
                elif line:
                    current_seq.append(line)
        

        if current_id is not None:
            sequences[current_id] = ''.join(current_seq)
        
        return sequences
    
    def predict_fasta(self, fasta_file):
        """
        
        Args:
            fasta_file: str
            
        Returns:
            dict: {seq_id: {'prediction': int, 'probability': float}}
        """
        sequences = self.read_fasta(fasta_file)
        results = {}
        
        for seq_id, sequence in sequences.items():
            prediction = self.predict(sequence)
            probability = self.predict_proba(sequence)
            results[seq_id] = {
                'prediction': prediction,
                'probability': probability
            }
        
        return results
