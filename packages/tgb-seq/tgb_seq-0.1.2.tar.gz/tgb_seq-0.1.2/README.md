
<img src="./logos/full_logo.svg">

## TGB-Seq Benchmark: Challenging Temporal GNNs with Complex Sequential Dynamics (ICLR 2025)
The **TGB-Seq benchmark** is designed to provide a comprehensive evaluation framework for temporal graph neural networks (GNNs), focusing on their ability to capture complex sequential dynamics.
- TGB-Seq offers datasets curated from diverse real-world dynamic interaction systems, inherently featuring intricate sequential dynamics and fewer repeated edges.
- TGB-Seq is available as a convenient pip package, offering seamless access to dataset downloading, negative sample generation and evaluation. We provide a quick-start example built on DyGLib, enabling easy integration.
- TGB-Seq adopts a standardized evaluation protocol with fixed dataset splits, generating 100 negative samples per test instance and computing the MRR metric for consistent and reliable performance assessment.

## Install
You can install TGB-Seq using Python package manager pip.

```shell
pip install tgb-seq
```

#### Requirements

- Python>=3.9
- numpy>2.0
- pandas>=2.2.3
- huggingface-hub>=0.26.0
- torch>=2.5.0


## Package Usage

### Quick Start
Get started with TGB-Seq using this quick-start example built on [DyGLib](https://github.com/yule-BUAA/DyGLib). Just follow the commands below to begin your journey with TGB-Seq! 🚀🚀🚀

```shell
pip install tgb-seq
git clone git@github.com:TGB-Seq/TGB-Seq.git
python examples/train_link_prediction.py --dataset_name GoogleLocal --model_name DyGFormer --patch_size 2 --max_input_sequence_length 64 --gpu 0 --batch_size 200 --dropout 0.1 --sample_neighbor_strategy recent
```

To submit your results to the [TGB-Seq leaderboard](https://TGB-Seq.github.io/leaderboard/), please fill in this [Google Form](https://forms.gle/dbhX8vVNzVTLU9pL8).

### Dataloader

For example, to load the Flickr dataset to `./data/`, run the following code:
```python
from tgb_seq.LinkPred.dataloader import TGBSeqLoader
data=TGBSeqLoader("Flickr", "./data/")
```
Then, Flickr.csv and Flickr_test_ns.npy will be downloaded from Hugging Face automatically into `./data/Flickr/`. The arrays of source nodes, destination nodes, interaction times, negative destination nodes for the test set can be accessed as follows.

```python
src_node_ids=data.src_node_ids
dst_node_ids=data.dst_node_ids
node_interact_times=data.node_interact_times
test_negative_samples=data.negative_samples
```

If you encounter any network errors when connecting to Hugging Face, you can use the Hugging Face mirror site to download the dataset. To do so, run the following command in your terminal:
```shell
export HF_ENDPOINT=https://hf-mirror.com
```

We also provide all the TGB-Seq datasets on [Google Drive](https://drive.google.com/drive/folders/1qoGtASTbYCO-bSWAzSqbSY2YgHr9hUhK?usp=sharing) and their original datasets [here](https://drive.google.com/drive/folders/1_WkYtmpGtxxf2XzzLlOzyzn6WUFkiGD-?usp=sharing).

### Evaluator
Up to now, all the TGB-Seq datasets are evaluated by the MRR metric. The evaluator takes `positive_probabilities` with size as `(batch_size,)` and `negative_probabilities` with size as `(batch_size x number_of_negatives)` as inputs and outputs the rank of eash positive sample with size as `(batch_size)`.
```python
from tgb_seq.LinkPred.evaluator import Evaluator 
evaluator=Evaluator()
result_dict=evaluator.eval(positive_probabilities,negative_probabilities)
```

## Citing TGB-Seq
If you use TGB-Seq datasets, please cite [our paper](https://openreview.net/forum?id=8e2LirwiJT).