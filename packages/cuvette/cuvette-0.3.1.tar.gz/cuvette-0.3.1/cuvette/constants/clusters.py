from dataclasses import dataclass
from typing import List


@dataclass
class Cluster:
    name: str
    clusters: List[str]
    description: str
    has_gpus: bool


CLUSTERS = [
    Cluster(
        name="Any CPU  (       CPU, 1wk lim, WEKA)",
        clusters=[
            # "ai2/phobos-cirrascale",
            "ai2/hammond",
        ],
        description="Any cluster supporting 1 week CPU sessions",
        has_gpus=False,
    ),
    Cluster(
        name="Any L40s ( 40GB L40s, 1dy lim, WEKA)",
        clusters=[
            "ai2/neptune-cirrascale",
            "ai2/triton-cirrascale",
        ],
        description="Any cluster with L40s or A100s",
        has_gpus=True,
    ),
    Cluster(
        name="Any A100 ( 80GB A100, 1dy lim, WEKA)",
        clusters=[
            "ai2/saturn-cirrascale",
        ],
        description="Any cluster with 1 week A100 sessions",
        has_gpus=True,
    ),
    Cluster(
        name="Any H100 ( 80GB H100, 4hr lim, WEKA)",
        clusters=[
            "ai2/ceres-cirrascale",
            "ai2/jupiter-cirrascale-2",
        ],
        description="Any cluster with 2 hour H100 sessions",
        has_gpus=True,
    ),
    Cluster(
        name="Any B200 (192GB B200, 4hr lim, WEKA)",
        clusters=[
            "ai2/titan-cirrascale",
        ],
        description="Any cluster with 2 hour B200 sessions",
        has_gpus=True,
    ),
    Cluster(
        name="Hammond  (       CPU, 1wk lim, WEKA)",
        clusters=["ai2/hammond"],
        description="Debugging and data transfers - No GPUs, Ethernet (50 Gbps/server), WEKA storage, 1 week timeout",
        has_gpus=False,
    ),
    Cluster(
        name="Phobos   (       CPU, 1wk lim, WEKA)",
        clusters=["ai2/phobos-cirrascale"],
        description="Debugging and data transfers - No GPUs, Ethernet (50 Gbps/server), WEKA storage, 1 week timeout",
        has_gpus=False,
    ),
    Cluster(
        name="Saturn   ( 80GB A100, 1dy lim, WEKA)",
        clusters=["ai2/saturn-cirrascale"],
        description="Small experiments before using Jupiter - 208 NVIDIA A100 (80 GB) GPUs, Ethernet (50 Gbps/server), WEKA storage, 1 week timeout",
        has_gpus=True,
    ),
    Cluster(
        name="Ceres    ( 80GB H100, 4hr lim, WEKA)",
        clusters=["ai2/ceres-cirrascale"],
        description="Small distributed jobs - 88 NVIDIA H100 GPUs (80 GB), 4x NVIDIA InfiniBand (200 Gbps/GPU), WEKA storage, 2 hour timeout",
        has_gpus=True,
    ),
    Cluster(
        name="Jupiter  ( 80GB H100, 4hr lim, WEKA)",
        clusters=["ai2/jupiter-cirrascale-2"],
        description="Large distributed jobs - 1024 NVIDIA H100 (80 GB) GPUs, 8x NVIDIA InfiniBand (400 Gbps/GPU), WEKA storage, 2 hour timeout",
        has_gpus=True,
    ),
    Cluster(
        name="Titan    (192GB B200, 4hr lim, WEKA)",
        clusters=["ai2/titan-cirrascale"],
        description="Distributed jobs - 96 NVIDIA B200 (192GB) GPUs, 8x NVIDIA InfiniBand (400 Gbps/GPU), 2 hour timeout",
        has_gpus=True,
    ),
    Cluster(
        name="Neptune  ( 40GB L40s, 1dy lim, WEKA)",
        clusters=["ai2/neptune-cirrascale"],
        description="Small experiments (≤ 40 GB memory) - 112 NVIDIA L40 (40 GB) GPUs, Ethernet (50 Gbps/server), WEKA storage, 1 week timeout",
        has_gpus=True,
    ),
    Cluster(
        name="Triton   ( 40GB L40s, 1dy lim, WEKA)",
        clusters=["ai2/triton-cirrascale"],
        description="Session-only - 16 NVIDIA L40 (40 GB) GPUs, Ethernet (50 Gbps/server), WEKA storage, 1 week timeout",
        has_gpus=True,
    ),
    Cluster(
        name="Augusta  ( 80GB H100, 4hr lim, GCS)",
        clusters=["ai2/augusta-google-1"],
        description="Large distributed jobs - 1280 NVIDIA H100 (80 GB) GPUs, TCPXO (200 Gbps/server), Google Cloud Storage, 2 hour timeout",
        has_gpus=True,
    ),
    Cluster(
        name="Neptune CPU",
        clusters=[
            "ai2/neptune-cirrascale",
        ],
        description="1 week CPU session",
        has_gpus=False,
    ),
    Cluster(
        name="Triton CPU",
        clusters=[
            "ai2/triton-cirrascale",
        ],
        description="1 week CPU session",
        has_gpus=False,
    ),
    Cluster(
        name="Saturn CPU",
        clusters=[
            "ai2/saturn-cirrascale",
        ],
        description="1 day CPU session",
        has_gpus=False,
    ),
]


NEW_CLUSTER_ALIASES = {
    "ai2/allennlp": "ai2/allennlp-elanding-a100-40g",
    "ai2/allennlp-dev-a100-sea": "ai2/allennlp-elanding-a100-40g",
    "ai2/augusta-batch-h100-dsm-tcpxo": "ai2/augusta-google-1",
    "ai2/augusta":"ai2/augusta-google-1",
    "ai2/ceres-dev-h100-aus-ib": "ai2/ceres-cirrascale",
    "ai2/ceres":"ai2/ceres-cirrascale",
    "ai2/jupiter-batch-h100-aus-ib": "ai2/jupiter-cirrascale-2",
    "ai2/jupiter":"ai2/jupiter-cirrascale-2",
    "ai2/neptune-dev-l40-aus": "ai2/neptune-cirrascale",
    "ai2/neptune":"ai2/neptune-cirrascale",
    "ai2/phobos-dev-aus": "ai2/phobos-cirrascale",
    "ai2/phobos":"ai2/phobos-cirrascale",
    "ai2/prior-dev-a6000-sea": "ai2/prior-elanding",
    "ai2/prior":"ai2/prior-elanding",
    "ai2/prior-rtx8000":"ai2/prior-elanding-rtx8000",
    "ai2/prior-dev-rtx8000-sea": "ai2/prior-elanding-rtx8000",
    "ai2/rhea-dev-a6000-aus": "ai2/rhea-cirrascale",
    "ai2/rhea":"ai2/rhea-cirrascale",
    "ai2/saturn-dev-a100-aus": "ai2/saturn-cirrascale",
    "ai2/saturn":"ai2/saturn-cirrascale",
    "ai2/titan-batch-b200-aus-ib": "ai2/titan-cirrascale",
    "ai2/titan":"ai2/titan-cirrascale",
    "ai2/triton-dev-l40-aus": "ai2/triton-cirrascale",
    "ai2/triton":"ai2/triton-cirrascale",
}