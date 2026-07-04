class Prompts:
    rules = """Please provide a detailed functional design specification in Markdown format that includes:
        ## 1. System Overview
        Brief description of the system/module and its primary purpose.
        ## 2. Purpose and Scope
        What the code is designed to accomplish and its boundaries.
        ## 3. Functional Requirements
        - Key functionalities and features
        - User interactions and use cases
        - Business logic requirements
        ## 4. System Architecture
        - High-level architectural components
        - Component relationships
        - Design patterns used
        ## 5. Data Flow
        - How data moves through the system
        - Input/output transformations
        - Data storage and retrieval
        ## 6. Key Components
        - Main classes, functions, and modules
        - Component responsibilities
        - Interface definitions
        ## 7. Dependencies and External Integrations
        - External libraries and frameworks
        - API dependencies
        - Third-party services
        ## 8. Input/Output Specifications
        - Expected inputs and formats
        - Output specifications
        - Error responses
        ## 9. Error Handling and Validation
        - Error handling strategies
        - Input validation rules
        - Exception management
        ## 10. Performance and Scalability
        - Performance considerations
        - Scalability factors
        - Resource requirements
        ## 11. Security Considerations
        Do a full security analysis and document the following:
        - Security measures implemented
        - Potential vulnerabilities
        - Access control mechanisms
        - If code follows all up-to-date cybersecurity standards
        - If applicable, if code follows all up-to-date pharma compliance's (like HIPPA)
        - Optimization and improvement suggestions - if there are any potential vulnerabilities, suggest fixes with code recommendations
        ## 12. Programming Standards Adherence
        - Per language standards (like PEP 8 for Python)
        ## 13. Summary of improvements/optimizations that could be made
        Use clear, professional language suitable for technical teams and stakeholders.
        Add recommendations for optimization and improvement in each section.
        Avoid using special Unicode characters that might cause encoding issues."""

    mermaid_rules = f"""STEP 1: Use ONLY this exact syntax patterns for Mermaid v11.8:
        flowchart TD
            A[Start Process] --> B{{Is Valid?}}
            B -->|Yes| C[Continue]
            B -->|No| D[Handle Error]
            C --> E[End]
            D --> E

        STEP 2: MANDATORY SYNTAX REQUIREMENTS:
        1. Start with exact diagram type keyword (flowchart TD)
        2. Use ONLY these node shapes: [Rectangle], {{Diamond}}
        3. Use ONLY these arrows: --> and -.-> for dotted. 
        4. Node IDs must be simple letters/numbers (A, B, C1, User, etc.)
        5. NO special characters in labels except spaces and basic punctuation (,.!?). NO quotes ever!
        6. Proper indentation (4 spaces)
        7. Do not use any Mermaid reserved words such as 'end'
        Generate ONLY the Mermaid script - no explanations, no code blocks, no markdown.
        The output must work in Mermaid v11.8 without any syntax errors.

        STEP 3: ADDITIONAL REQUIREMENTS
        1. When calling a function specifically mention in the flowchart that a function is being called
        2. In the "Start" step, instead of labeling it 'start' mention the input arguments. For example: 'Input: Arg1'.
        3. In the "End" step, instead of labeling it 'end' mention what the code segment returns. For example: 'Output: result'. If the code doesn't return anything, put 'Output: None'. 
        4. When calling a function, specify what arguments the function is being called with.
        5. Keep function calls separate from logic split blocks.
        6. If function calls are chained, they MUST be separated into different logical blocks.
        7. NEVER use parentheses ()
        8. Logical splits phrased as questions MUST have a question mark (?)
        9. When referencing a variable, specify its type. Use this format: 'variable str'
        10. DO NOT modify the existing code flow. 
        11. Every node and arrow in the diagram must correspond directly to a real statement or logical step in the provided code. Do not invent or infer steps that are not present.
        12. You MUST use solid arrows (-->) when moving logically forward in the flow chart and use dotted arrows (-->) when moving in reverse or when looping back to the start of a loop.
        13. If a flow requires a dotted arrow (e.g., for reverse or loop-back), you MUST replace the existing solid arrow with a dotted one, NOT add a new arrow between the same nodes.
        14. Do not create multiple arrows (solid and dotted) between the same nodes pointing the same direction.
        15. Before finalizing the diagram, check that every step and arrow is justified by the code. If the code is trivial, the diagram should be minimal.
        16. Do NOT treat 'self' as a function call, variable, or node in the diagram. It is a conventional reference to the instance or class and should not appear as a step, call, or node in the flowchart.

        STEP 4: CLASS SPECIFICATIONS
        IMPORTANT: DO NOT include a class definition list in your response, that will be added automatically later. 
        Still, label elements with the following classes:
        Assign start blocks the 'startBlock' class.
        Assign end blocks the 'endBlock' class.
        Assign function calls the 'functionCall' class.
        Assign logic splits the 'logicSplit' class.
        Intermediary steps MUST not be assigned a class.
        Add color legend palet to each mermaid diagram text.
    """

    full_bom_streamlit_code = open("bom_streamlit_full_code_string.txt", "r", encoding="utf-8").read()


    functional_specification_prompts = f"""
        You are a senior software architect and technical documentation expert. Analyze the following code and create a comprehensive functional design specification for the given code.
        Code to analyze:
    ############################# CODE START #############################

        {full_bom_streamlit_code}

    ############################# CODE END #############################

        ***RULES:
        {rules}
        """


    full_code_analysis_prompt = f"""
        You are a senior software architect and technical documentation expert. Analyze the following code and create a comprehensive functional design specification.
        Code to analyze:

        ##############################CODE START###################################

        {full_bom_streamlit_code}

        ###############################CODE END####################################

        ***RULES:
        {rules}
        """

    get_api_list_prompt = f"""You are a senior software architect and software developer. Analyze the provided source code and extract all HTTP API endpoints. Scan for common frameworks and patterns including but not limited to: Flask (`@app.route`, `app.add_url_rule`, Blueprints), FastAPI (`@app.get`, `@router.post`, `include_router`), Django (`urlpatterns`, `path`, `re_path`, `View`, `APIView`, `ViewSet`), Django REST Framework (`@api_view`, `Router.register`), and generic decorator or function-based routing patterns. Also detect class-based endpoints where methods map to HTTP verbs.
        Rules:
        1. Return ONLY a JSON array and nothing else. No explanation, no markdown, no code fences.
        2. Each array item must be an object with keys exactly: `api_name`, `path`, `method`.
        3. `api_name` must be the route string as declared in code (preserve path parameters as written).
        4. `path` must be the full file path relative to the repository root where the endpoint is defined.
        5. `method` must be one of `GET`, `POST`, `PUT`, `DELETE`. If an endpoint explicitly supports multiple methods, emit one object per method. If the method cannot be determined, set `method` to `UNKNOWN`.
        6. Detect methods declared via decorator names (`get`, `post`, `put`, `delete`), decorator `methods` argument (e.g., `methods=['GET','POST']`), `add_url_rule` `methods` parameter, or class method names mapped in frameworks (e.g., `get` method on Django REST `APIView`). Match case-insensitively.
        7. If routes are registered via routers/blueprints with a prefix, combine the prefix and route to form the `api_name` when both are visible in the provided code snippet; if the prefix is not visible, use the declared sub-route as-is.
        8. Ignore non-HTTP handlers (e.g., CLI commands, background jobs).
        9. Remove duplicates so each `api_name`+`path`+`method` tuple is unique.
        10. Ensure output is valid JSON (arrays and objects properly formed, double quotes).

        Example output format:
        [
            {{
                "api_name": "/login",
                "path": "project_name/core/services/heart_beat.py",
                "method": "POST"
            }}
        ]

        Code to analyze:
        {full_bom_streamlit_code}
        and return the JSON array of endpoints only.
"""

    get_mermaid_prompt = f"""
        You are a software architecture expert specializing in visual documentation using Mermaid v11.8.
        CRITICAL: You MUST generate ONLY valid Mermaid v11.8 syntax. Follow these exact requirements:
        Analyze the following code and generate a detailed code flow diagram in Mermaid format.
        If there are multiple arrows between the same nodes, remove the redundant ones and ensure only the correct arrow type remains.
        If the diagram contains steps not present in the code, remove them.

        Code to analyze:
        ############################CODE START###########################

        {full_bom_streamlit_code}

        ############################CODE START###########################

        RULES
        {mermaid_rules}
        """

    def get_functional_specification_prompt(code: str, rules=rules):
        return f"""
            You are a senior software architect and technical documentation expert. Analyze the following code and create a comprehensive functional design specification for the given code.
            Code to analyze:
        ############################# CODE START #############################

        {code}

        ############################# CODE END #############################

        ***RULES:
        {rules}
            """