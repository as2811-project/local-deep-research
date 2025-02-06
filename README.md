### Local Deep Research

This is a very basic attempt to recreate the Deep Research functionalities introduced by OpenAI/Google Gemini, locally. Running the notebook will let you provide your research objectives
and specify how wide you want the research to be. Depending upon the model, you will see a 'research_report.md' file in your project directory within minutes.

#### Prerequisites

Ollama running with any language model
API keys from SERP API and Firecrawl

#### How to run

1. Clone the repo
2. Run `pip install -r requirments`
3. Create a .env file with the following: SERP_API_KEY, FIRECRAWL_API_KEY, MODEL (use the model's name from Ollama as is)
4. Open the jupyter notebook and click run all

#### Performance

This notebook was written and tested on a Macbook Pro M1Pro with 16GB RAM. Deepseek R1 7b, Llama 3.1 8b, Phi3 3.8b produced truly terrible outputs. None of them fully adhered to the
instructions. Phi4 (14b) however stays relatively close to my prompts and produces an output that some might consider 'usable'. I personally thought it was acceptable but not detailed
enough. This might have to do with model sizes or the way they were trained. Bigger models might result in better results. 

#### TODO

[] Improve naming: Variables could be renamed to be more descriptive/precise
[] Clean up: Remove logging statements
[] Shift away from a single Jupyter notebook to a full blown FastAPI endpoint
[] Add a front-end
