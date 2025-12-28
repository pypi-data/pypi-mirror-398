from al_inference_engine.syntax import Concept

FREEVARANY_CONCEPT = Concept('FREEVARANY')
BOOL_CONCEPT: Concept = Concept("Bool")  # 布尔
COMPLEX_NUMBER_CONCEPT = Concept("ComplexNumber")
EQUATION_CONCEPT = Concept("Equation", "仅用于表示算术方程")


# Example Concepts
example_concept_1: Concept = Concept("Person_Example")
example_concept_2: Concept = Concept("Color_Example")
example_concept_3: Concept = Concept("Location_Example")
example_concept_4: Concept = Concept("Object_Example")
