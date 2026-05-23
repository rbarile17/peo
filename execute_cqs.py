from pathlib import Path

from rdflib import Graph, Literal, Namespace, RDF, URIRef

BASE = "http://www.semanticweb.org/robertobarile/ontologies/2026/4/untitled-ontology-11"
NS = Namespace(BASE + "#")
ORIGINAL = Path("peo.owl")
COPY = Path("peo_augmented.owl")


def build_augmented_graph() -> Graph:
    g = Graph()
    g.parse(str(ORIGINAL), format="xml")

    # ABox additions to make the queries executable and meaningful without changing the TBox.
    g.add((NS["task1"], RDF.type, NS["Task"]))
    g.add((NS["architecture1"], RDF.type, NS["Architecture"]))
    g.add((NS["constraint1"], RDF.type, NS["Constraint"]))
    g.add((NS["constraint1"], NS["variable"], Literal("test")))
    g.add((NS["constraint1"], NS["operator"], Literal("equals")))
    g.add((NS["constraint1"], NS["constraintValue"], Literal("test")))

    g.add((NS["model"], RDF.type, NS["FoundationModel"]))
    g.add((NS["model2"], RDF.type, NS["FoundationModel"]))
    g.add((NS["model3"], RDF.type, NS["FoundationModel"]))

    g.add((NS["prompting_technique1"], RDF.type, NS["PromptingTechnique"]))
    g.add((NS["prompt1"], RDF.type, NS["Prompt"]))
    g.add((NS["prompt2"], RDF.type, NS["Prompt"]))
    g.add((NS["response1"], RDF.type, NS["Response"]))

    g.add((NS["prompt1"], NS["adoptsSuitableTechniqueFor"], NS["task1"]))
    g.add((NS["prompting_technique1"], NS["isAdoptedIn"], NS["prompt1"]))
    g.add((NS["prompting_technique1"], NS["isConsideredSuitableFor"], NS["task1"]))

    g.add((NS["chat1"], NS["hasMessage"], NS["prompt1"]))
    g.add((NS["chat1"], NS["hasMessage"], NS["response1"]))
    g.add((NS["chat1"], NS["hasMessage"], NS["prompt2"]))

    g.add((NS["prompt1"], NS["isInChatWithFoundationModel"], NS["model"]))
    g.add((NS["response1"], NS["isInChatWithFoundationModel"], NS["model"]))
    g.add((NS["prompt2"], NS["isInChatWithFoundationModel"], NS["model"]))

    g.serialize(destination=str(COPY), format="xml")
    return g


def format_term(term):
    if isinstance(term, URIRef):
        return str(term).rpartition("#")[-1]
    return str(term)


def run_query(g: Graph, query: str, title: str):
    print(f"\n=== {title} ===")
    rows = list(g.query(query))
    if not rows:
        print("No results")
        return
    for row in rows:
        print(" | ".join(format_term(value) for value in row))


if __name__ == "__main__":
    graph = build_augmented_graph()

    run_query(
        graph,
        """
        PREFIX : <http://www.semanticweb.org/robertobarile/ontologies/2026/4/untitled-ontology-11#>
        SELECT DISTINCT ?task WHERE {
          ?task a :Task .
        }
        ORDER BY STR(?task)
        """,
        "CQ1 - What are the tasks?",
    )

    run_query(
        graph,
        """
        PREFIX : <http://www.semanticweb.org/robertobarile/ontologies/2026/4/untitled-ontology-11#>
        SELECT DISTINCT ?task WHERE {
          ?task a :Task ;
                :targetDataModality ?modality .
          FILTER(STR(?modality) = "image")
        }
        ORDER BY STR(?task)
        """,
        "CQ2 - What tasks exist for a given data modality?",
    )

    run_query(
        graph,
        """
        PREFIX : <http://www.semanticweb.org/robertobarile/ontologies/2026/4/untitled-ontology-11#>
        SELECT DISTINCT ?constraint ?variable ?operator ?value WHERE {
          :task1 :hasConstraint ?constraint .
          OPTIONAL { ?constraint :variable ?variable }
          OPTIONAL { ?constraint :operator ?operator }
          OPTIONAL { ?constraint :constraintValue ?value }
        }
        ORDER BY STR(?constraint)
        """,
        "CQ3 - What are the constraints of a given task?",
    )

    run_query(
        graph,
        """
        PREFIX : <http://www.semanticweb.org/robertobarile/ontologies/2026/4/untitled-ontology-11#>
        SELECT DISTINCT ?architecture WHERE {
          ?model a :FoundationModel ;
                 :hasArchitecture ?architecture .
        }
        ORDER BY STR(?architecture)
        """,
        "CQ4 - What are the possible foundation model architectures?",
    )

    run_query(
        graph,
        """
        PREFIX : <http://www.semanticweb.org/robertobarile/ontologies/2026/4/untitled-ontology-11#>
        SELECT DISTINCT ?model ?variantOrEvolution WHERE {
          {
            ?model :hasEvolution ?variantOrEvolution .
          }
          UNION
          {
            ?model :hasVariant ?variantOrEvolution .
          }
        }
        ORDER BY STR(?model) STR(?variantOrEvolution)
        """,
        "CQ5 - What are the variants and evolutions of a given foundation model?",
    )

    run_query(
        graph,
        """
        PREFIX : <http://www.semanticweb.org/robertobarile/ontologies/2026/4/untitled-ontology-11#>
        SELECT DISTINCT ?modality WHERE {
          :model :supportedDataModality ?modality .
        }
        ORDER BY STR(?modality)
        """,
        "CQ6 - What data modalities can a given foundation model process?",
    )

    run_query(
        graph,
        """
        PREFIX : <http://www.semanticweb.org/robertobarile/ontologies/2026/4/untitled-ontology-11#>
        SELECT DISTINCT ?prompt WHERE {
          :prompting_technique1 :isAdoptedIn ?prompt .
        }
        ORDER BY STR(?prompt)
        """,
        "CQ7 - What prompts are based on a given prompting technique?",
    )

    run_query(
        graph,
        """
        PREFIX : <http://www.semanticweb.org/robertobarile/ontologies/2026/4/untitled-ontology-11#>
        SELECT DISTINCT ?response WHERE {
          ?response :directlyFollows :prompt1 .
        }
        ORDER BY STR(?response)
        """,
        "CQ8 - What is the response to a given prompt?",
    )

    run_query(
        graph,
        """
        PREFIX : <http://www.semanticweb.org/robertobarile/ontologies/2026/4/untitled-ontology-11#>
        SELECT (AVG(?prompt_count) AS ?avg_prompts) (AVG(?response_count) AS ?avg_responses)
        WHERE {
          {
            SELECT ?chat (COUNT(DISTINCT ?prompt) AS ?prompt_count)
            WHERE {
              ?chat a :Chat ;
                    :hasMessage ?prompt .
              ?prompt a :Prompt .
            }
            GROUP BY ?chat
          }
          {
            SELECT ?chat (COUNT(DISTINCT ?response) AS ?response_count)
            WHERE {
              ?chat a :Chat ;
                    :hasMessage ?response .
              ?response a :Response .
            }
            GROUP BY ?chat
          }
        }
        """,
        "CQ9 - How many prompts and responses are there on average per chat?",
    )

    run_query(
        graph,
        """
        PREFIX : <http://www.semanticweb.org/robertobarile/ontologies/2026/4/untitled-ontology-11#>
        SELECT DISTINCT ?model WHERE {
          ?chat a :Chat ;
                :hasMessage :prompt1 ;
                :isHeldWith ?model .
        }
        ORDER BY STR(?model)
        """,
        "CQ10 - Which foundation model is a given prompt submitted to?",
    )

    run_query(
        graph,
        """
        PREFIX : <http://www.semanticweb.org/robertobarile/ontologies/2026/4/untitled-ontology-11#>
        SELECT ?model (COUNT(DISTINCT ?chat) AS ?chat_count)
        WHERE {
          ?chat a :Chat ;
                :isHeldWith ?model .
        }
        GROUP BY ?model
        ORDER BY DESC(?chat_count) STR(?model)
        """,
        "CQ11 - How many chats were conducted per model?",
    )

    run_query(
        graph,
        """
        PREFIX : <http://www.semanticweb.org/robertobarile/ontologies/2026/4/untitled-ontology-11#>
        SELECT DISTINCT ?prompt WHERE {
          :prompting_technique1 :isAdoptedIn ?prompt .
          :prompting_technique1 :isConsideredSuitableFor :task1 .
        }
        ORDER BY STR(?prompt)
        """,
        "CQ12 - Which prompts are based on a prompting technique considered suitable for the targeted task?",
    )

    run_query(
        graph,
        """
        PREFIX : <http://www.semanticweb.org/robertobarile/ontologies/2026/4/untitled-ontology-11#>
        SELECT DISTINCT ?technique WHERE {
          ?technique a :PromptingTechnique .
        }
        ORDER BY STR(?technique)
        """,
        "CQ12 (Prompting Techniques) - What are the prompting techniques?",
    )

    run_query(
        graph,
        """
        PREFIX : <http://www.semanticweb.org/robertobarile/ontologies/2026/4/untitled-ontology-11#>
        SELECT DISTINCT ?technique WHERE {
          ?technique a :PromptingTechnique ;
                     :isConsideredSuitableFor :task1 .
        }
        ORDER BY STR(?technique)
        """,
        "CQ13 - What prompting techniques are suitable for a given task?",
    )

    run_query(
        graph,
        """
        PREFIX : <http://www.semanticweb.org/robertobarile/ontologies/2026/4/untitled-ontology-11#>
        SELECT DISTINCT ?technique WHERE {
          ?technique a :PromptingTechnique ;
                     :isConsideredSuitableFor ?task .
          ?task :targetDataModality ?modality .
          FILTER(STR(?modality) = "image")
        }
        ORDER BY STR(?technique)
        """,
        "CQ14 - What prompting techniques are suitable for tasks targeting a given data modality?",
    )

    run_query(
        graph,
        """
        PREFIX : <http://www.semanticweb.org/robertobarile/ontologies/2026/4/untitled-ontology-11#>
        SELECT DISTINCT ?technique WHERE {
          ?technique a :PromptingTechnique ;
                     :isConsideredSuitableFor ?task .
          ?task :hasConstraint ?constraint .
          ?constraint :variable ?var .
          FILTER(STR(?var) = "test")
        }
        ORDER BY STR(?technique)
        """,
        "CQ15 - What prompting techniques are suitable for tasks with a constraint on a given variable?",
    )
