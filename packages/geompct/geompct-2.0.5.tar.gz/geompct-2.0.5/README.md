# Accurate Pentagon Copying Test (PCT) evaluation using Combinatorial Optimization and Geometric Theory

`pct-eval` is a research-oriented Python package for evaluating the Pentagon Copying Test (PCT) using classical computer vision and computational geometry. The project explores whether the structural and spatial properties required to assess a pentagon copying task can be captured directly through geometric reasoning, without relying on large deep learning models or complex feature pipelines.

### Motivation and Scope
The motivation behind this work comes from a growing trend in the literature to apply heavyweight deep learning architectures to PCT evaluation. Many existing approaches extract high-dimensional features [1, 5], repeatedly downsample and upsample representations, and depend on opaque models that are difficult to interpret. For a task that is fundamentally geometric in nature, this complexity is often unnecessary. Angles, intersections, edge relations, and spatial consistency can be described explicitly using well-established geometric principles and classical computer vision techniques [2, 3]. Nonetheless, recent studies [4] have shown that even state-of-the-art multimodal large language models struggle with shape understanding, highlighting the limitations of purely data-driven approaches for geometry-centric tasks [5].

This repository is built on the hypothesis that a lightweight, interpretable algorithm is not only sufficient for evaluating the Pentagon Copying Test, but in many cases preferable. By operating directly on geometric properties, the evaluation process remains transparent and aligned with clinical reasoning. Each decision made by the algorithm can be inspected, explained, and traced back to concrete geometric constraints rather than latent representations.

The emphasis on lightweight computation is particularly important for long-term and real-world use. Applications targeting elderly populations benefit from algorithms that are efficient, stable, and easy to deploy on low-power or edge devices. Reducing computational cost also improves sustainability and lowers maintenance complexity, making the approach more suitable for longitudinal monitoring and real-world clinical support systems.

While the current focus of this project is on geometric structure and spatial accuracy, the framework naturally opens the door to additional research directions. In particular, analyzing the force, pressure, and stroke dynamics of hand-drawn inputs may provide further insight into motor control and cognitive decline. These aspects are especially relevant in the context of dementia research, where both drawing structure and execution quality can reflect disease progression. Future extensions of this work will explore how such signals can be integrated alongside geometric evaluation.

This package is intended as a research and evaluation tool. It does not perform diagnosis and is not designed to replace clinical judgment. Instead, it aims to provide a transparent and reproducible computational framework that can support neuropsychological research and the development of explainable assessment systems.

---

## Installation

Create and activate a Python environment, then install the required dependencies.

```bash
conda create -n pct-eval python=3.10 -y
conda activate pct-eval
pip install -r requirements.txt
```

Or install directly via pip:

```bash
pip install pct-eval
```

Note that this package requires **Python 3.10 or higher**.

<!-- ---

## Basic Usage

```python
import geompct

image = geompct.io.load_image("sample_pct.png")
processed = geompct.preprocessing.process(image)
geometry = geompct.geometry.extract(processed)
score, details = geompct.evaluate(geometry)

print("Score:", score)
print("Details:", details)
```

The API is designed to expose intermediate representations so that the full evaluation pipeline remains inspectable and explainable.

--- -->

## Usage

The main function to evaluate a Pentagon Copying Test (PCT) image is `eval_pct`. Below is an example of how to use it:

```python
from geompct.eval import eval_pct
eval_pct(
    OUTPUT_DIR = "results/",
    IMG_SHAPE = (500, 500),
    fpath="path/to/your/pct_image.jpg"
)
```

* `OUTPUT_DIR`: Directory where the results will be saved.
* `IMG_SHAPE`: Tuple specifying the desired image shape (height, width).
* `fpath`: File path to the PCT image to be evaluated.

## License

This project is released under the MIT License. See the `LICENSE` file for details.

---

## References

[1] Maruta J, Uchida K, Kurozumi H, Nogi S, Akada S, Nakanishi A, Shinoda M, Shiba M, Inoue K. Deep convolutional neural networks for automated scoring of pentagon copying test results. Sci Rep. 2022 Jun 14;12(1):9881. doi: 10.1038/s41598-022-13984-7. PMID: 35701481; PMCID: PMC9198090.

[2] Pengfei Zheng, Wilson Byiringiro, Weiwei Xie, Zhengkai Jiang, Can Cui, Yongjun Wu; An improved Harris corner detection method for honeycomb structures. AIP Advances 1 April 2025; 15 (4): 045028. https://doi.org/10.1063/5.0254564

[3] Kim N, Truty T, Duke Han S, Heo M, Buchman AS, Bennett DA, Tasaki S. Digital quantification of the MMSE interlocking pentagon areas: a three-stage algorithm. Sci Rep. 2024 Apr 19;14(1):9038. doi: 10.1038/s41598-024-59194-1. PMID: 38641631; PMCID: PMC11031600.

[4] Park I, Kim YJ, Kim YJ, Lee U. Automatic, Qualitative Scoring of the Interlocking Pentagon Drawing Test (PDT) based on U-Net and Mobile Sensor Data. Sensors (Basel). 2020 Feb 27;20(5):1283. doi: 10.3390/s20051283. PMID: 32120879; PMCID: PMC7085787.

[5] Rudman, W., Golovanevsky, M., Bar, A., Palit, V., LeCun, Y., Eickhoff, C., & Singh, R. (2025). Forgotten polygons: Multimodal large language models are shape-blind (arXiv preprint arXiv:2502.15969). https://arxiv.org/abs/2502.15969


## Contact
For questions or feedback, feel free to open an issue on the GitHub repository: https://github.com/htdgv/memocare-imgprocx/issues 