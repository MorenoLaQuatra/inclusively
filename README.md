# Inclusively demo

This repository contains the Flask application that powers the [Inclusively](#) platform demo.
This demo has been accepted for presentation at the [ECML PKDD 2023 - Demo Track](https://2023.ecmlpkdd.org/).

## What is Inclusively?

Inclusively is a platform that aims at developing deep learning models that can detect and correct non-inclusive language.

It leverages an NLP pipeline that includes:

- **Detection**: Detecting non-inclusive language in a text.
- **Rewriting**: If some non-inclusive language is detected, the model will rewrite the text to make it inclusive.

## How does it work?

The platform is composed of 4 main pages:

- **Home**: The home page of the platform. It contains a brief description of the platform and a link to the demo.
- **Testing**: The testing page. It contains the demo itself and the possibility to insert the text to be corrected by Inclusively.
- **Evaluation**: The evaluation page. It allows users to evaluate the correctness of the corrections made by Inclusively. Each user can provide a feedback for each correction at sentence level.
- **Explanation**: The explanation page. It contains the output of explainability methods applied to the model. It can allow *data scientists* to understand how the model works and how it makes its decisions.

## Screenshots

**Home page**

![Home page](demo_screenshots/home.png)

**Assistant page**

![Assistant page](demo_screenshots/assistant.png)

**Evaluation and Annotation page**

![Evaluation page](demo_screenshots/annotation.png)

**Explanation page**

![Explanation page](demo_screenshots/explain.png)

## Supported languages

- 🇮🇹 Italian 
- [WIP] 🇫🇷 French   
- [WIP] 🇪🇸 Spanish

## Citation

```bibtex
Citation will be available soon after proceedings publication.
```

# People behind Inclusively
- **Moreno La Quatra** - [Homepage](https://mlaquatra.me) - [GitHub](https://github.com/MorenoLaQuatra) - [Twitter](https://twitter.com/MorenoLaQuatra)
- **Salvatore Greco** - [Homepage]() - [GitHub]()
- **Luca Cagliero** - [Homepage]()
- **Tania Cerquitelli** - [Homepage]()