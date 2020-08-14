# Awesome Pretrained StyleGAN2

A collection of pre-trained [StyleGAN2](https://github.com/NVlabs/stylegan2) models trained on different datasets at different resolution.

_See [this repo](https://github.com/justinpinkney/awesome-pretrained-stylegan) for pretrained models for StyleGAN 1_

{% for model in models %}
[![](content/{{ model.name | replace(" ", "%20") }}/thumbnail.jpg)](#{{ model.name | replace(" ", "-") | replace("(", "")  | replace(")", "")}}){% endfor %}

If you have a publically accessible model which you know of, or would like to share please see the [contributing](#contributing) section. _Hint: the simplest way to submit a model is to fill in this [form](https://forms.gle/PE1iiTa5tNTdBFYN9)._

### Table of Contents

- Models
{% for model in models %}
    - [{{ model.name }}](#{{ model.name | replace(" ", "-") | replace("(", "")  | replace(")", "") }}){% endfor %}
- [Notes](#notes)
- [Contributing](#contributing)

{% for model in models %}
## {{ model.name }}

![](content/{{ model.name | replace(" ", "%20")}}/samples.jpg)
- [Style mixing example](content/{{ model.name | replace(" ", "%20")}}/mixing.jpg), [interpolation video](content/{{ model.name | replace(" ", "%20")}}/interpolation.mp4)
- Dataset: {{ model.dataset }}
- Resolution: {{ model.resolution }} config: {{ model.config }}
- Author: [{{ model.author }}]({{ model.author_url }})
- [Download link]({{ model.download_url }})
- StyleGAN2 implementation: {{ model.implementation }}{% if model.Notes %}
- Notes: {{ model.Notes }}{% endif %}
- Licence: {{ model.license }}
- [Source]({{ model.source_url }})

{% endfor %}

## Notes

- The configuration "slim" refers to the reduced feature map model used in the Karras limited data and Zhao data efficient papers.
- Each row in the sample grids above use a different level of trunction: 0.25, 0.5, 0.75, 1 from top to bottom.
- Style mixing figure and interpolation video generated using truncation of 0.75

## Contributing

__TLDR: You can either edit the [models.json](models.json) file or fill out this [form](https://forms.gle/PE1iiTa5tNTdBFYN9).__

This readme is automatically generated using Jinja, please do not try and edit it directly. Information about the models is stored in `models.json` please add your model to this file. Preview images are generated automatically and the process is used to test the link so please only edit the json file.