
import os
import requests
from ollama import chat
from ollama import ChatResponse
from firecrawl import FirecrawlApp
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
from IPython.display import display, Markdown
load_dotenv()

SERP_API_KEY = os.getenv("SERP_API_KEY")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
MODEL = os.getenv("MODEL")


def fetch_serp(q: str):
    url = 'https://serpapi.com/search'
    params = {
        'api_key': SERP_API_KEY,
        'engine': 'google',
        'q': q,
        'google_domain': 'google.com',
        'hl': 'en'
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        json_response = response.json()
        organic = json_response['organic_results']
        formatted_results = []
        for result in organic:
            title = result['title']
            link = result['link']
            description = result['snippet']
            resource_object = {
                'title': title,
                'link': link,
                'description': description
            }
            formatted_results.append(resource_object)
        return formatted_results


app = FirecrawlApp(api_key=FIRECRAWL_API_KEY)


def retrieve_context(url: str):
    context = app.scrape_url(url, params={'formats': ['markdown']})
    return context


class SearchQueries(BaseModel):
    queries: list[str]


user_prompt = input("Topic of Research: ")
research_objective = input("Research objective: ")
research_width = input("Width of Research (1-5): ")


def generate_queries(prompt: str, objective: str, width: str):
    generated_queries: ChatResponse = chat(model=MODEL, messages=[
        {
            'role': 'user',
            'content': f"Given the user's prompt, generate {width} search queries (to be used as Google Search queries) that will get you started with performing deep research on the topic in hand. It is important that the queries you generate are unique and have ZERO overlap with each other. The number of search queries you are asked to generate defines the width of the user's research. Do not generate anything else apart from the {width} queries required. Here's the user's research title:{prompt}. And here's the research objective: {objective}. Your thought process while generating these queries should consider the main objective of the research, and you should figure out how to progressively.",
        },
    ],
        format=SearchQueries.model_json_schema())
    formatted_queries = SearchQueries.model_validate_json(
        generated_queries.message.content)
    return formatted_queries


search_results = []
current_queries = generate_queries(
    user_prompt, research_objective, research_width)
for q in current_queries.queries:
    results = fetch_serp(q)
    search_results.extend(results)


class ResultItem(BaseModel):
    title: str
    link: str


class RelevantQueries(BaseModel):
    r_queries: list[ResultItem]


def evaluate_relevance(prompt: str, objective: str, width: str, serp_results):
    relevant_queries: ChatResponse = chat(model=MODEL, messages=[
        {
            'role': 'user',
            'content': f"You are an expert data extractor. You are provided with a list of search results for a specific research query. This will be a list of objects containing the title, description and the link to an article/webpage. Use the title and description to verify if a particular search result is indeed relevant to the query. Return the titles AND links that are relevant to the research objective in the specified format. Here is the list of search results: {serp_results}. Here's the user's topic of research: {prompt}. The objective of the research is as follows: {objective}. You must return {width} results from the list that has been provided to you"
        }
    ], format=RelevantQueries.model_json_schema())
    formatted_relevant_queries = RelevantQueries.model_validate_json(
        relevant_queries.message.content)
    return formatted_relevant_queries


research_context = []
evaluated_queries = evaluate_relevance(
    user_prompt, research_objective, research_width, search_results)
for item in evaluated_queries.r_queries:
    print(f"Retrieving research context for the resource: {item.title}")
    c = retrieve_context(item.link)
    research_context.append(c.get("markdown", ""))


class ContextEval(BaseModel):
    further_research: bool
    probing_queries: Optional[list[SearchQueries]]


def evaluate_context(prompt: str, objective: str, context: list[str], width: int) -> tuple[bool, Optional[list[str]]]:
    """Evaluates whether further research is needed based on the current context."""
    research_status: ChatResponse = chat(model=MODEL, messages=[
        {
            'role': 'user',
            'content': f"""
            You are an expert information extractor. You are provided with information regarding the user's topic of research, which is: {user_prompt}.
            The objective of this research is: {research_objective}.
            The research context we have until now is here: {research_context}.
            Based on the given information, confirm if further research is required.
            However, if you think more information is required for a comprehensive report, generate {width} more probing questions
            that go deeper into the topic, but make sure the queries are specific and precise to the current context as they will be used
            to fetch Google search results, which in turn will be used for further research.
            """
        }
    ], format=ContextEval.model_json_schema())

    context_eval = ContextEval.model_validate_json(
        research_status.message.content)
    return context_eval.further_research, context_eval.probing_queries


def research_loop(prompt: str, objective: str, context: list[str], width: int) -> list[str]:
    """Manages the iterative research process to refine the research context."""
    max_iterations = 2  # Prevent infinite loops
    iteration_count = 0

    while iteration_count < max_iterations:
        further_research, probing_queries = evaluate_context(
            user_prompt, research_objective, research_context, width)

        if not further_research:
            break  # Stop generating more questions, proceed to report generation

        iteration_count += 1
        new_search_results = []
        for _ in probing_queries:
            new_search_results.extend(fetch_serp(_.title))
        search_results.extend(new_search_results)
        evaluate_new_results = evaluate_relevance(
            user_prompt, research_objective, research_width, new_search_results)
        for _ in evaluate_new_results.r_queries:
            print(f"Retrieving research context for the resource: {_.title}")
            new_context = retrieve_context(_.link)
            research_context.extend(new_context.get("markdown", ""))

    if iteration_count >= max_iterations:
        print("Max iterations reached. Proceeding with the available research context.")
    return research_context


def generate_report(prompt: str, objective: str, context: list[str], sources: list[str], width: int) -> str:
    final_report: ChatResponse = chat(model=MODEL, messages=[
        {
            'role': 'user',
            'content': f"""You are an expert analyst. Your job is to use the provided research prompt, objective and context to generate a clear and comprehensive report.
            User Prompt: {prompt}
            Research Objective: {objective}
            Research Context: {context}
            With this information, generate a report as instructed. Be sure to include all sources, persons, objects etc in the report. You MUST include a references section and appropriately add citations. The report must be in markdown format. You are allowed to take liberties with section titles and in-report formatting."""
        }
    ])
    return final_report.message.content


def main():
    user_prompt = input("Topic of Research: ")
    research_objective = input("Research objective: ")
    research_width = input("Width of Research (1-5): ")
    research_context = research_loop(
        user_prompt, research_objective, research_context, research_width)
    report = generate_report(user_prompt, research_objective,
                             research_context, search_results, research_width)
    display(Markdown(report))
