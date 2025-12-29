from melody_features import get_all_features
from melody_features.corpus import get_corpus_files

first_ten = get_corpus_files("essen", max_files=10)
features = get_all_features(first_ten, skip_idyom=False)
features.to_csv("output.csv", index=False)
print(features.iloc[1:2,].to_json(indent=4, orient="records"))
print("Number of columns:", features.shape[1])
