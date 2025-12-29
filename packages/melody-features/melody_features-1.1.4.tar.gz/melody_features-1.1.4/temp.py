from melody_features.features import get_all_features, ioi_standard_deviation
from melody_features.representations import Melody

the_lick = Melody(midi_data={"MIDI Sequence": "Note(start=0.0, end=1.0, pitch=62, velocity=100)Note(start=1.0, end=2.0, pitch=64, velocity=100)Note(start=2.0, end=3.0, pitch=65, velocity=100)Note(start=3.0, end=4.0, pitch=67, velocity=100)Note(start=4.0, end=5.5, pitch=64, velocity=100)Note(start=5.5, end=6.5, pitch=60, velocity=100)Note(start=6.5, end=7.5, pitch=62, velocity=100)"})
res = get_all_features("/Users/davidwhyatt/feature_set/src/melody_features/corpora/essen_folksong_collection/appenzel.mid", skip_idyom=True)
print(res.head())

print(ioi_standard_deviation(the_lick.starts))