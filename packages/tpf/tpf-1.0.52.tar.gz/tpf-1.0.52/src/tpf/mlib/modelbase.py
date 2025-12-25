
import joblib
# import torch 
from tpf.d1 import pkl_load,pkl_save 


class ModelBase:
    dl_name_list = ["dlseqone","seqonedl","seqone"]
    def __init__(self):
        pass
    @classmethod
    def model_load(cls, model_path, model=None, params=None,alg_name=None):
        """深度学习参数文件以.dict保存 
        """
        if alg_name is not None and alg_name in ["seqone"]:
            from tpf.mlib.seq import SeqOne
            seq_len    = params["seq_len"]
            model = SeqOne(seq_len=seq_len, out_features=2)
        elif model_path.endswith(".dict"):
            import torch 
            if model is None:
                if "seqone" in model_path.lower():
                    from tpf.mlib.seq import SeqOne
                    seq_len    = params["seq_len"]
                    model = SeqOne(seq_len=seq_len, out_features=2)
            model.load_state_dict(torch.load(model_path,weights_only=False))
        else:
            model = pkl_load(file_path=model_path, use_joblib=True)
        return model

    @classmethod
    def model_save(cls,model, model_path, alg_name=None):
        if model_path.endswith(".dict") or (alg_name is not None and alg_name in cls.dl_name_list):
            import torch 
            torch.save(model.state_dict(), model_path)
        else:
            pkl_save(model, file_path=model_path, use_joblib=True)

    