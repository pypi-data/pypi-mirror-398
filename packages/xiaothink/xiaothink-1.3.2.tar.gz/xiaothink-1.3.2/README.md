# Xiaothink Python Module Usage Documentation

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
Xiaothink is an AI research organization focused on Natural Language Processing (NLP), dedicated to training advanced on-device models with limited data and computing resources. The Xiaothink Python module is our core toolkit, covering various functions such as text-based Q&A, multimodal Q&A, image compression, sentiment classification, and more. Below is the detailed usage guide and code examples.

## Table of Contents
1. [Installation](#installation)
2. [Local Dialogue Models](#local-dialogue-models)
3. [Image Feature Extraction and Multimodal Dialogue](#image-feature-extraction-and-multimodal-dialogue)
4. [Image Compression to Feature Technology (img_zip)](#image-compression-to-feature-technology-img_zip)
5. [Sentiment Classification Tool](#sentiment-classification-tool)
6. [AI Rate Detection Tool](#ai-rate-detection-tool)
7. [Changelog](#changelog)

---

## Installation

First, you need to install the Xiaothink module via pip:

```bash
pip install xiaothink
```

---

## License

This project is licensed under the Apache License, Version 2.0 - see the [LICENSE](LICENSE) file for details.

The [NOTICE](NOTICE) file contains additional attribution information for the proprietary technologies included in this module.

---

## Local Text-only Dialogue Models

For locally loaded dialogue models, you should call the corresponding function according to the model type.

### Single-turn Dialogue (to be removed in future versions)

Suitable for single-turn dialogue scenarios.

### Example Code

```python
import xiaothink.llm.inference.test_formal as tf

model = tf.QianyanModel(
    ckpt_dir=r'path/to/your/t6_model',
    MT='t6_beta_dense',
    vocab=r'path/to/your/vocab'# vocab file is provided in the model repository
)

while True:
    inp = input('[Q]: ')
    if inp == '[CLEAN]':
        print('[Context Cleared]\n\n')
        model.clean_his()
        continue
    re = model.chat_SingleTurn(inp, temp=0.32)  # Use chat_SingleTurn for single-turn dialogue
    print('\n[A]:', re, '\n')
```

### Multi-turn Dialogue

Suitable for multi-turn dialogue scenarios.

### Example Code

```python
import xiaothink.llm.inference.test_formal as tf

model = tf.QianyanModel(
    ckpt_dir=r'path/to/your/t6_model',
    MT='t6_beta_dense',
    vocab=r'path/to/your/vocab'# vocab file is provided in the model repository
)

while True:
    inp = input('[Q]: ')
    if inp == '[CLEAN]':
        print('[Context Cleared]\n\n')
        model.clean_his()
        continue
    re = model.chat(inp, temp=0.32)  # Use chat for multi-turn dialogue
    print('\n[A]:', re, '\n')
```

### Text Continuation

Suitable for more flexible text continuation scenarios.

### Example Code

```python
import xiaothink.llm.inference.test as test

MT = 't6_beta_dense'
m, d = test.load(
    ckpt_dir=r'path/to/your/t6_model',
    MT='t6_beta_dense',
    vocab=r'path/to/your/vocab'# vocab file is provided in the model repository
)

inp='Hello!'
belle_chat = '{"conversations": [{"role": "user", "content": {inp}}, {"role": "assistant", "content": "'.replace('{inp}', inp)    # Instruct format supported by instruction-tuned models in the T6 series
inp_m = belle_chat

ret = test.generate_texts_loop(m, d, inp_m,    
                               num_generate=100,
                               every=lambda a: print(a, end='', flush=True),
                               temperature=0.32,
                               pass_char=['▩'])    # ▩ is the <unk> token for T6 series models
```

**Important Note**: For local models, it is recommended to use the `model.chat` function for multi-turn dialogue. For pre-trained models without instruction tuning, it is recommended to use the `test.generate_texts_loop` function. **The single-turn dialogue function `model.chat_SingleTurn` will be removed in future versions.**

---

## Image Feature Extraction and Multimodal Dialogue

### Dual-vision Solution

In version 1.2.0, we introduced an innovative dual-vision solution:
1. **Image Compression to Feature (img_zip)**: Convert images to text tokens that can be inserted anywhere in the dialogue.
2. **Native Vision Encoder**: Pass the latest image to the native vision model's vision encoder (standard approach).

This solution achieves:
- Detailed analysis of the latest single image based on the native vision encoder
- Understanding of multiple images in the context based on img_zip technology
- Significant reduction in computing resource requirements

### Vision Model Usage Guidelines

For vision-enabled models, regardless of whether there is image input, you should use the following code:

```python
from xiaothink.llm.inference.test_formal import QianyanModel

if __name__ == '__main__':
    model = QianyanModel(
        ckpt_dir=r'path/to/your/vision_model',
        MT='t6_standard_vision',  # Note: model type is vision model
        vocab=r'path/to/your/vocab.txt',
        imgzip_model_path='path/to/img_zip/model.keras'  # Specify img_zip model path
    )

    temp = 0.28  # Temperature parameter
    
    while True:
        inp = input('[Q]: ')
        if inp == '[CLEAN]':
            print('[Context Cleared]\n\n')
            model.clean_his()
            continue
        # Use chat_vision for dialogue
        ret = model.chat_vision(inp, temp=temp, pre_text='', pass_start_char=[])
        print('\n[A]:', ret, '\n')
```

**Important Notes**:
- Vision models must use the `chat_vision` method; do not use `chat` (which is only for text-only models)
- You must prepare an img_zip image compression encoder model that matches the vision model
- Mismatched models will cause the model to fail to understand the meaning of encoded tokens

### Image Processing Interfaces

Two new image processing interfaces have been added:

1. **img2ms** (for non-native vision models):
   ```python
   description = model.img2ms('path/to/image.jpg', temp=0.28)
   print(description)
   ```

2. **img2ms_vision** (for native vision models):
   ```python
   description = model.img2ms_vision('path/to/image.jpg', temp=0.28, max_shape=224)
   print(description)
   ```

### Image Reference Syntax

In dialogue, use the following syntax to reference images:
```python
<img>image path or URL</img>Please describe this image
```

The model will automatically parse the image path, extract features, and answer based on the image content.

**Notes**:
1. Image paths should use absolute paths to ensure correct parsing
2. Native vision models only support analyzing the most recent image
3. img_zip technology supports referencing multiple images in the context

---

## Image Compression to Feature Technology (img_zip)

The `img_zip` module provides advanced image and video compression/decompression functions based on deep learning feature extraction technology. Below are the detailed usage methods:

### 1. Command-line Interactive Mode

```bash
python -m xiaothink.llm.img_zip.img_zip
```

After running, you will enter an interactive command-line interface:

```
===== img_zip Image Video Compression Tool =====
Please enter .keras model path: path/to/your/imgzip_model.keras
Model loaded successfully!

Please select a function:
1. Compress image
2. Decompress image
3. Compress video
4. Decompress video
0. Exit

Please select (0-6):
```

### 2. Python Code Invocation

```python
from xiaothink.llm.img_zip.img_zip import ImgZip

# Initialize instance
img_zip = ImgZip(model_path='path/to/your/imgzip_model.keras')

# Compress image
compressed_path = img_zip.compress_image(
    img_path='input.jpg',
    patch=True,  # Whether to use patch processing
    save_path='compressed_img'  # Save path prefix
    ability=0.02,# New feature in 1.2.5: Set custom compression rate to 0.02 (when ability is 0, it means not using custom compression rate). The algorithm calculates and compresses to a close size (there may be errors between theoretical calculation and actual size)
)

# Generates two files: compressed_img.npy and compressed_img.shape

# Decompress image
img_zip.decompress_image(
    compressed_input='compressed_img',  # Compressed file prefix
    patch=True,  # Whether to use patch processing
    save_path='decompressed.jpg'  # Output path
)

# Compress video
compressed_paths, metadata_path = img_zip.compress_video(
    video_path='input.mp4',
    output_dir='compressed_video',  # Output directory
    patch=True  # Whether to use patch processing
)

# Decompress video
img_zip.decompress_video(
    compressed_dir='compressed_video',  # Compressed file directory
    output_path='decompressed.mp4'  # Output path
)

# Convert image to array and save
img_array = img_zip.image_to_array('input.jpg')
img_zip.save_image_array(img_array, 'image_array.npy')

# Load image from array
loaded_array = img_zip.load_image_array('image_array.npy')
img = img_zip.array_to_image(loaded_array)
img.save('restored.jpg')
```

### 3. Key Function Descriptions

1. **Compress Image** (`compress_image`)
   - `patch=True`: Split large images into 80x80 patches for separate processing
   - Outputs two files: `.npy` (feature vectors) and `.shape` (original size information)

2. **Decompress Image** (`decompress_image`)
   - Requires both `.npy` and `.shape` files
   - Automatically restores original dimensions

3. **Video Processing** (`compress_video`/`decompress_video`)
   - Automatically extracts video frames and processes them in batches
   - Preserves original video frame rate and resolution information
   - Uses temporary directories for intermediate file processing

#### 4. Parameter Descriptions

| Parameter | Type | Description |
|-----------|------|-------------|
| `model_path` | str | Path to img_zip model (.keras file) |
| `patch` | bool | Whether to use patch processing (default: True) |
| `save_path` | str | Output file path prefix |
| `img_path` | str | Input image path |
| `video_path` | str | Input video path |
| `output_dir` | str | Output directory path |
| `output_path` | str | Output file path |

#### 5. Processing Flow Features

1. **Patch Processing**:
   - Automatically splits large images into 80x80 patches
   - Each patch is independently encoded into feature vectors
   - Preserves original size information

2. **Video Processing**:
   - Automatically extracts frames and processes them in batches
   - Preserves original video parameters (fps, resolution)
   - Uses temporary directories for intermediate file processing

3. **Progress Display**:
   - All operations come with detailed progress bars
   - Displays current processing step and remaining time

4. **Error Handling**:
   - Comprehensive exception catching mechanism
   - Detailed error information prompts

#### 6. Usage Recommendations

1. For images larger than 80x80, it is recommended to use patch processing (`patch=True`)
2. Video processing requires sufficient disk space for temporary frame files
3. Ensure the input model matches the processing task
4. Use absolute paths to avoid file location issues

This module is the core component of Xiaothink vision models (especially non-native ones). Based on efficient image feature representation and compression, it can enable any text-only AI model to have basic vision capabilities through fine-tuning.

---

## Sentiment Classification Tool

The sentiment classification tool is based on loaded dialogue models and provides text sentiment tendency analysis functionality, which can quickly determine the sentiment category of input text (e.g., positive, negative, neutral, etc.).

### Feature Description
- This tool is a customized interface based on Xiaothink framework (Xiaothink T6 series, etc.) models
- Implements sentiment classification based on Xiaothink framework language models without the need to load additional classification models
- Supports input of ultra-long text and returns sentiment analysis results
- It is recommended to use single-turn dialogue enhanced models, such as: Xiaothink-T6-0.15B-ST

### Usage Example

```python
from xiaothink.llm.inference.test_formal import *
from xiaothink.llm.tools.classify import *

if __name__ == '__main__':
    # Initialize basic dialogue model
    model = QianyanModel(
        ckpt_dir=r'path/to/your/t6_model',  # Model weight directory  It is recommended to use _ST version models
        MT='t6_standard',  # Model type (must match weights)
        vocab=r'path/to/your/vocab.txt',  # Vocabulary path
        use_patch=0  # Do not use patch processing (text-only model)
    )
    
    # Initialize sentiment classification model (depends on basic dialogue model)
    cmodel = ClassifyModel(model)
    
    # Loop input text for sentiment classification
    while True:
        inp = input('Enter text: ')
        res = cmodel.emotion(inp)  # Call sentiment classification interface
        print(res)  # Output sentiment analysis results
```

### Notes
1. The sentiment classification model depends on an initialized `QianyanModel`; ensure the base model is loaded successfully
2. It is recommended to use instruction-tuned models (e.g., `t6_standard`); non-tuned models may affect classification accuracy
3. The output result format is: {'Positive': 0.6667, 'Negative': 0.1667, 'Neutral': 0.1667}

---
## AI Rate Detection Tool
The AI rate detection tool is based on loaded detection models and provides text AI generation probability analysis functionality. It can accurately determine the AI generation probability of each character in the text, output the overall AI rate average, and return detailed character-level detection information, achieving comprehensive traceability analysis of text AI generation traces.

### Feature Description
- This tool is a customized interface based on Xiaothink framework (Xiaothink T series, etc.) models
- Implements text AI rate analysis based on Xiaothink framework detection models without the need to load independent detection models
- Supports ultra-long text detection and batch text detection, returning multi-dimensional complete detection results
- Can output **four levels of results: overall AI rate average, detection conclusion, probability statistics information, and character-level detailed information**

### Usage Example
```python
if __name__ == "__main__" and 1:
    # 1. Initialize detector
    detector = AIDetector(
        ckpt_dir=r'E:\Xiaothink Framework\Paper\ganskchat\ckpt_test_t7',
        model_type='t7',
        print_load_info=True
    )

    # 2. Detect text
    test_texts = [
        "This is a sentence that a car repair blogger active on mobile internet used to start many of his videos before being sued by BYD. Finally, this 'most miserable repairman in history' has received the first-instance judgment of being sued by BYD.",
        "\"Isn't it,\" Grandma looked up at the osmanthus tree, her eyes filled with gentle memories, \"This was planted by your grandfather back then, almost thirty years ago. At that time, he said, planting an osmanthus tree, it will bloom in autumn, fragrant and beautiful, and when we have children, we can make osmanthus cake to eat.\"",
        "These days, my heart has been quite unsettled. Sitting in the yard enjoying the cool air tonight, I suddenly thought of the lotus pond I pass by every day. In this moonlight of the full moon, it should have a different appearance. The moon gradually rose higher, and the laughter of children on the road outside the wall could no longer be heard; my wife was patting Run'er inside the house, humming a lullaby drowsily. I quietly put on my large shirt and went out the door."
    ]

    # 3. Execute detection
    for text in test_texts:
        print(f"\n{'='*60}")
        print(f"Detected Text: {text}")
        result = detector.detect_ai_rate(text)
        
        print(f"AI Rate (Probability Average): {result['AI Rate (Probability Average)']}")
        print(f"Detection Conclusion: {result['Detection Conclusion']}")
        print(f"Probability Statistics: Min={result['Probability Statistics']['Minimum Probability']} | Max={result['Probability Statistics']['Maximum Probability']}")
        
        # Optional: Print character-level details
        print("\nCharacter-level Details:")
        for detail in result['Character-level Details']:
            print(f"  Position {detail['Character Position']}: Previous Text 「{detail['Complete Previous Text']}」→ Character 「{detail['Target Character']}」→ Probability {detail['Prediction Probability']}")

    # 4. Release resources
    detector.close()
```

### Notes
1. When initializing the AI rate detector, ensure `ckpt_dir` points to the correct T7 series model weight directory; otherwise, model loading will fail
2. **Core Accuracy Note**: This tool has **relatively accurate** AI rate detection results for **small model-generated text**, which can meet the traceability needs of small model-generated content; however, it has poor AI rate detection effect for **large model-generated text**, and the detection results have low reference value. It is strictly prohibited to use this tool for AI determination scenarios of large model-generated content
3. After detection is completed, you must call the `detector.close()` method to release resources such as video memory and hardware handles to avoid memory leaks and excessive video memory usage caused by long-term operation
4. Character-level details are optional output items. For ultra-long text of ten thousand characters, printing these details will significantly increase output time and can be selectively printed according to actual needs
5. When detecting a large number of texts in batches, it is recommended to process them in batches according to text length to avoid detection lag caused by passing too many ultra-long texts in a single batch
6. Enabling `print_load_info=True` when loading the model allows you to view loading progress and hardware adaptation information, which is convenient for troubleshooting model loading exceptions

---
Xiaothink framework series model names, their corresponding MT (model architecture version), and form (model prompt input format) list:
| Model Name (by release time)              | mt parameter           | form parameter   |
|-----------------------|------------------|-------------|
| Xiaothink-T7-ART(0.07B)| mt='t7_cpu_standard'    | form=1 |
| Xiaothink-T6-0.08B       | mt='t6_beta_dense'| form=1      |
| Xiaothink-T6-0.15B       | mt='t6_standard' | form=1      |
| Xiaothink-T6-0.02B       | mt='t6_fast'     | form=1      |
| Xiaothink-T6-0.5B        | mt='t6_large'    | form=1      |
| Xiaothink-T6-0.5B-pretrain| mt='t6_large'    | form='pretrain' |

---

## Changelog
### Version 1.3.2 (2025-12-27)
- **Updated Interfaces**:
  - Added "AI Rate Detection" interface based on Xiaothink-T series models.
- **New Models**:
  - Added support for MT architectures "t7" and "t7_cpu_standard" in the Xiaothink-T7 series models.

### Version 1.3.1 (2025-10-31)
- **Updated Interfaces**:
  - Added custom input shape (must be supported by the corresponding model) for vision-related interfaces instead of the fixed 80*80*3 in previous versions
  - The ImgZIP command-line interface also added custom input shape (must be supported by the corresponding model) instead of the fixed 80*80*3 in previous versions, and added comprehensive quality scores based on SNR, PSNR, and SSIM.

### Version 1.3.0 (2025-10-17)[Yanked]
- **New Models**:
  - Added support for the Xiaothink-T7 series model architecture.

### Version 1.2.5 (2025-09-02)
- **Updated Interfaces**:
  - Added "custom compression rate" function to the ImgZIP command-line interface, supporting other compression rates beyond the model's native compression rate (implemented based on calculating and scaling the original image).

### Version 1.2.4 (2025-08-30)
- **Updated Interfaces**:
  - Updated the import method of ImgZIP-related interfaces in the documentation to: from xiaothink.llm.img_zip.img_zip import ImgZip

### Version 1.2.3 (2025-08-30)
- **New Features**:
  - Added Xiaothink-T6-0.02B series models (MT='t6_fast')
  - Added Xiaothink-T6-0.5B series models (MT='t6_large')
  - Added support for form='pretrain' in the model.chat method. For instruction-tuned models in the T6 series, form=1 should be used; for pre-trained models, form='pretrain' should be used

### Version 1.2.2 (2025-08-18)
- **New Features**:
  - Added sentiment classification tool to implement text sentiment tendency analysis through `ClassifyModel`
  - Added `xiaothink.llm.tools.classify` module to support sentiment classification based on basic dialogue models
  - Provided `cmodel.emotion(inp)` interface to return real-time text sentiment results

### Version 1.2.1 (2025-08-16)
- **New Models**:
  - Added Xiaothink-T6-0.15B series models (MT='t6_standard')

### Version 1.2.0 (2025-08-08)
- **Breakthrough Innovation**:
  - Added support for native vision models using an innovative dual-vision solution
  - Dual-path processing of image compression to feature tokens (img_zip) + native vision encoder
  - Retains multi-image context understanding capability while achieving single-image detail analysis

- **New Interfaces**:
  - `model.chat_vision`: Specialized dialogue interface for vision models
  - `model.img2ms`: Image description interface for non-native vision models
  - `model.img2ms_vision`: Image description interface for native vision models (supports max_shape parameter)
  
- **Module Expansion**:
  - Added `xiaothink.llm.img_zip.img_zip` command-line tool
  - Supports compression and decompression of images and videos
  - Provides rich parameters to adjust compression quality

- **Usage Guidelines**:
  - Vision models must use the `chat_vision` method
  - Must use a matching img_zip encoder model
  - Image paths should use absolute paths

### Version 1.1.0 (2025-08-02)
- **New Features**:
  - Added `img2ms` and `ms2img` interfaces to achieve high compression ratio lossy compression of images
  - Supports converting images into AI-readable feature tokens
  - Extended dialogue models to support multimodal input (image + text)
  - In test_formal, it supports converting feature tokens generated by multimodal AI into images and saving them to the system temporary folder by default.
  
- **Technical Upgrades**:
  - Based on Xiaothink framework's self-developed img_zip technology
  - Supports intelligent compression of 80x80x3 image patches
  - When outputting 96 feature values, combined with .7z algorithm, it can achieve an ultra-high compression ratio of 10%
  
- **Usage Method**:
  - Insert images using the `<img>{image_path}</img>` tag in dialogue
  - Need to specify the img_zip model path when initializing the model
  - Supports multimodal dialogue (image description, image Q&A, and other scenarios)

---

The above covers the main functions and usage methods of the Xiaothink Python module.

If you have any questions or suggestions, please feel free to contact us: xiaothink@foxmail.com.