Here are several interesting AI projects using case-based reasoning (CBR) with Python, leveraging the cbrkit or cbrlib libraries to help manage cases and similarity measures. [1, 2]  
Project Ideas 

• Medical Diagnostic Assistant 

	• Concept: Build a system that helps diagnose medical conditions by comparing a new patient's symptoms and history to a database of previous cases (symptoms, diagnosis, treatment, and outcome). 
	• Python Implementation: Use a library like  cbrkit 
 to store anonymized patient cases. Implement similarity measures for different symptoms (e.g., fever level, duration) and retrieve the most relevant past diagnoses to suggest potential outcomes. A GitHub project focused on diabetes management provides a relevant example. 

• Customer Support Chatbot 

	• Concept: Create a chatbot for customer service that solves user problems by retrieving and adapting solutions from a knowledge base of past support queries and their resolutions. 
	• Python Implementation: The case base would store problem descriptions and successful solutions. When a new query comes in, the system uses NLP (with libraries like spaCy or NLTK) to analyze the text and find similar past cases. The stored solution is then adapted (e.g., updating software version numbers in instructions) and presented to the user. 

• Recipe Recommendation System 

	• Concept: Develop a system that suggests recipes based on user preferences and available ingredients, learning from successful past cooking experiences. 
	• Python Implementation: Cases could be specific recipes with ingredient lists, steps, and user ratings. The system would calculate the similarity between a user's current ingredients/preferences and the case base. The "reuse" phase involves adapting the recipe (e.g., substituting an ingredient) to fit the new situation, and successful new adaptations can be retained in the case base. 

• Legal Case Precedent Analysis 

	• Concept: Design a tool that assists legal professionals by identifying relevant past court cases (precedents) to support arguments for a new case. 
	• Python Implementation: The system would store complex legal rulings and their outcomes. It would use advanced similarity measures to compare the facts of a new case to the existing precedents. A Python package specifically for legal case-based reasoning is a direct application of this idea. 

• IT Troubleshooting Assistant 

	• Concept: Automate the troubleshooting process for common technical issues by comparing a user's problem to a database of known issues and their solutions. 
	• Python Implementation: The case base could contain details like the type of device, operating system, error code, and the fix that worked. Simple similarity algorithms (like k-nearest neighbors) can be used to find the most similar past problems and recommend solutions. [3, 4, 5, 6, 7, 8]  

Useful Python Libraries 

• cbrkit: A modern, modular, and type-hinted Python toolkit for building CBR applications, available on PyPI. 
• cbrlib: A straightforward case-based reasoning library for Python that integrates with native Python classes for similarity calculations. 
• scikit-learn: Provides the k-nearest neighbors (k-NN) algorithm, a common machine learning algorithm used in simpler CBR systems for classification and regression tasks. [1, 2, 4, 9, 10]  

AI responses may include mistakes.

[1] https://pypi.org/project/cbrkit/
[2] https://github.com/cdein/cbrlib
[3] https://thedecisionlab.com/reference-guide/philosophy/case-based-reasoning
[4] https://artint.info/2e/html2e/ArtInt2e.Ch7.S7.html
[5] https://github.com/topics/case-based-reasoning?l=python&o=asc&s=forks
[6] https://pythonforlaw.com/2023/07/02/legal-case-based-reasoning.html
[7] https://artint.info/html1e/ArtInt_190.html
[8] https://www.ionos.com/digitalguide/websites/web-development/case-based-reasoning/
[9] https://dl.acm.org/doi/abs/10.1007/978-3-031-63646-2_19
[10] https://sebastianraschka.com/resources/ml-lectures-1/


Server running at http://127.0.0.1:8000/docs with all 26,872 Bitext cases loaded and vector cache warm. To avoid the port conflict in future, use --reload only during development and always clear the port first with kill $(lsof -ti:8000).


Yes, Case-Based Reasoning (CBR) can and often does use ontologies to significantly enhance its capabilities. Integrating ontologies provides a formal, semantic structure to define case features, relationships, and domain knowledge, leading to better case representation, improved retrieval, and more accurate adaptation of solutions. [1, 2, 3]  
Key benefits and applications of Ontology-Based Case-Based Reasoning (OBCBR) include: 

• Enhanced Knowledge Representation: Ontologies allow for a more comprehensive representation of a domain's concepts and relationships. 
• Improved Retrieval Accuracy: By using Semantic Web technologies (like OWL), systems can better understand the context and relationships between cases, rather than relying solely on keyword matching. 
• Better Semantic Search: Ontologies facilitate semantic retrieval, which is crucial for finding similar cases, particularly in complex domains like medicine or emergency response. 
• Structured Case Base: Cases can be stored as instances within an ontology, allowing for easier, structured, and more efficient management of past experiences. 
• Improved Adaptation: Semantic knowledge provided by ontologies can be used to adapt past solutions to fit new, slightly different problems. [1, 3, 4, 5, 6, 7, 8]  

Examples of Use: 

• Medical Diagnosis: A fuzzy ontology-based CBR system was used for diagnosing stomach-related illnesses, improving accuracy by leveraging domain-specific medical knowledge. 
• Emergency Response: An ontology-supported CBR (OS-CBR) system was implemented to assist in emergency, or crisis management. 
• Project Management: An enterprise architecture ontology (e.g., ArchiMEO) can be used to retrieve relevant historical project data. [3, 6, 9]  

In summary, ontologies bridge the gap between structured, domain-specific knowledge and the flexible, experience-based nature of CBR. [10]  

AI responses may include mistakes.

[1] https://ceur-ws.org/Vol-3723/paper20.pdf
[2] https://link.springer.com/chapter/10.1007/978-3-031-22938-1_10
[3] https://www.sciencedirect.com/science/article/abs/pii/S0167923613000043
[4] https://pmc.ncbi.nlm.nih.gov/articles/PMC11500847/
[5] https://link.springer.com/article/10.1007/s10506-008-9070-8
[6] https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0309722
[7] https://www.sciencedirect.com/science/article/pii/S0167923613000043
[8] https://link.springer.com/article/10.1007/s11423-025-10488-9
[9] https://www.tandfonline.com/doi/full/10.1080/17517575.2016.1161239
[10] https://thesai.org/Downloads/Volume6No11/Paper_26-Case_Based_Reasoning_Case_Representation_Methodologies.pdf

