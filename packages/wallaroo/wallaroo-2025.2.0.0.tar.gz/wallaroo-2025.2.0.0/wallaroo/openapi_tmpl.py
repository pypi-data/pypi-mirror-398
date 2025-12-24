import base64
import re

import pyarrow as pa  # type: ignore
import yaml

WITH_OPENAI = """
openapi: 3.1.1
info:
  title: {pipeline_name}
  description: |
    The Wallaroo Inference API allows you to perform real-time inference on deployed machine learning models and pipelines.
        
    ## OpenAI Compatibility
    
    Wallaroo provides OpenAI-compatible endpoints for seamless integration with existing OpenAI workflows:
    - **Completions API**: Text completion compatible with OpenAI's legacy completions API
    - **Chat Completions API**: Chat completion compatible with OpenAI's chat completions API
    
    ## Authentication
    
    All requests require authentication using Bearer tokens obtained through the Wallaroo platform.
    
  version: {version}

servers:
  - url: {url}
    description: Wallaroo Platform API

paths:
  /openai/v1/completions:
    post:
      summary: OpenAI-compatible text completion
      description: |
        OpenAI-compatible text completion endpoint. This endpoint provides the ability to use standard [OpenAI Completions API](https://platform.openai.com/docs/api-reference/completions) requests, or use the official OpenAI of compatible SDKs (e.g., lightllm) for pipelines configured to be OpenAI compatible.
        
        As this functionality is provided by the vLLM framework, the request and response schemas as outlined in the [vLLM Documentation](https://docs.vllm.ai/en/v0.6.6/serving/openai_compatible_server.html#completions-api).

      operationId: openaiCompletion
      tags:
        - OpenAI Compatibility
      requestBody:
        required: true
        content:
          application/json:
            examples:
              simple_completion:
                summary: Simple text completion
                description: |
                  A standard [OpenAI Completion API](https://platform.openai.com/docs/api-reference/completions) request, that also supports [vLLM's extra parameters](https://docs.vllm.ai/en/v0.6.6/serving/openai_compatible_server.html#completions-api).

                  The only deviation from the standard OpenAI/vLLM API is that the `model` property is optional. Its value, even if provided is ignored, since the model is determined by the pipeline.
                value:
                  model: "my_pipeline"
                  prompt: "The capital of France is"
                  max_tokens: 50
                  temperature: 0.7
              streaming_text_completion:
                summary: Text completion with Token Streaming
                description: |
                  A standard [OpenAI Completions API](https://platform.openai.com/docs/api-reference/completions) request, that also supports [vLLM's extra parameters](https://docs.vllm.ai/en/v0.6.6/serving/openai_compatible_server.html#completions-api).

                  The only deviation from the standard OpenAI/vLLM API is that the `model` property is optional. Its value, even if provided is ignored, since the model is determined by the pipeline.
                value:
                  model: "my_pipeline"
                  prompt: "The capitals of the countries of Europe are"
                  max_tokens: 200
                  temperature: 0.7
                  stream: true
      responses:
        '200':
          description: Successful completion
          content:
            application/json:
              examples:
                completion_response:
                  summary: Completion response
                  description: |
                    A standard [OpenAI Completions API](https://platform.openai.com/docs/api-reference/completions) response.
                  value:
                    id: "cmpl-abc123"
                    object: "completion"
                    created: 1677652288
                    model: "my_pipeline"
                    choices:
                      - text: " Paris."
                        index: 0
                        finish_reason: "stop"
                        logprobs: null
                    usage:
                      prompt_tokens: 5
                      completion_tokens: 2
                      total_tokens: 7
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '404':
          $ref: '#/components/responses/NotFound'
        '409':
          description: Pipeline type conflict
          content:
            application/json:
              description: Pandas records format response
              schema:
                $ref: '#/components/responses/Conflict'
              example:
                code: 409
                status: error
                error: "Inference failed. Please apply the appropriate OpenAI configurations to the models deployed in this pipeline. For additional help contact support@wallaroo.ai or your Wallaroo technical representative."
                source: engine
        '500':
          $ref: '#/components/responses/InternalServerError'
        '503':
          $ref: '#/components/responses/ServiceUnavailable'

  /openai/v1/chat/completions:
    post:
      summary: OpenAI-compatible chat completion
      description: |
        OpenAI-compatible text completion endpoint. This endpoint provides the ability to use standard [OpenAI Completions API](https://platform.openai.com/docs/api-reference/chat/create) requests, or use the official OpenAI of compatible SDKs (e.g., lightllm) for pipelines configured to be OpenAI compatible.
        
        As this functionality is provided by the vLLM framework, the request and response schemas as outlined in the [vLLM Documentation](https://docs.vllm.ai/en/v0.6.6/serving/openai_compatible_server.html#chat-api).
      operationId: openaiChatCompletion
      tags:
        - OpenAI Compatibility
      requestBody:
        required: true
        content:
          application/json:
            examples:
              simple_chat:
                summary: Simple chat completion
                description: |
                  A standard [OpenAI Completion API](https://platform.openai.com/docs/api-reference/chat/create) request, that also supports [vLLM's extra parameters](https://docs.vllm.ai/en/v0.6.6/serving/openai_compatible_server.html#chat-api).

                  The only deviation from the standard OpenAI/vLLM API is that the `model` property is optional. Its value, even if provided is ignored, since the model is determined by the pipeline.
                value:
                  model: ""
                  messages:
                    - role: "user"
                      content: "What is the capital of France?"
                  max_tokens: 50
                  temperature: 0.7
              streaming_simple_chat:
                summary: Chat completion with Token Streaming
                description: |
                  A standard [OpenAI Chat Completions API](https://platform.openai.com/docs/api-reference/chat/create) request, that also supports [vLLM's extra parameters](https://docs.vllm.ai/en/v0.6.6/serving/openai_compatible_server.html#chat-api).

                  The only deviation from the standard OpenAI/vLLM API is that the `model` property is optional. Its value, even if provided is ignored, since the model is determined by the pipeline.
                value:
                  model: ""
                  messages:
                    - role: "user"
                      content: "What is the capital of France?"
                  max_tokens: 50
                  temperature: 0.7
                  stream: true
      responses:
        '200':
          description: Successful chat completion
          content:
            application/json:
              examples:
                chat_response:
                  summary: Chat completion response
                  description: |
                    A standard [OpenAI Chat Completions API](https://platform.openai.com/docs/api-reference/chat/create) response.
                  value:
                    id: "chatcmpl-abc123"
                    object: "chat.completion"
                    created: 1677652288
                    model: ""
                    choices:
                      - message:
                          role: "assistant"
                          content: "The capital of France is Paris."
                        index: 0
                        finish_reason: "stop"
                        logprobs: null
                    usage:
                      prompt_tokens: 12
                      completion_tokens: 8
                      total_tokens: 20
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '404':
          $ref: '#/components/responses/NotFound'
        '409':
          description: Successful inference result
          content:
            application/json:
              description: Pandas records format response
              schema:
                $ref: '#/components/responses/Conflict'
              example:
                code: 409
                status: error
                error: "Inference failed. Please apply the appropriate OpenAI configurations to the models deployed in this pipeline. For additional help contact support@wallaroo.ai or your Wallaroo technical representative."
                source: engine
        '500':
          $ref: '#/components/responses/InternalServerError'
        '503':
          $ref: '#/components/responses/ServiceUnavailable'

components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: |
        Authentication token obtained through the Wallaroo platform.
        Use the SDK authentication methods to obtain a valid token.
        
  schemas:
    ErrorResponse:
      type: object
      properties:
        code:
          type: integer
          description: HTTP status code
          example: 400
        status:
          type: string
          description: Error status message
          example: "error"
        error:
          type: string
          description: Detailed error message
          example: "Invalid input format"
        source:
          type: string
          description: Source of the error (e.g., engine, sidekick)
          example: "engine"
      required:
        - code
        - error
        
  responses:
    BadRequest:
      description: Invalid request format or parameters
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
          examples:
            invalid_tensor:
              summary: Invalid tensor format
              value:
                code: 400
                status: "error"
                error: "tensor values may not be null"
                source: "engine"
                
    Unauthorized:
      description: Authentication required or invalid
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
          example:
            code: 401
            status: "error"
            error: "Jwt is missing"
            source: "platform"
            
    NotFound:
      description: Deployment or pipeline not found
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
          example:
            code: 404
            status: "error"
            error: "Deployment not found"
            source: "platform"
            
    Conflict:
      description: Endpoint doesn't match pipeline type
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'

    InternalServerError:
      description: Internal server error
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
          example:
            code: 500
            status: "error"
            error: "Internal processing error"
            source: "engine"
            
    ServiceUnavailable:
      description: Service temporarily unavailable or insufficient resources
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
          examples:
            pipeline_being_activated:
              summary: Pipeline being activated
              value:
                code: 503
                status: "error"
                error: "The resources required to run this request are not available. Please check the inference endpoint status and try again"
                source: "engine"
    

security:
  - BearerAuth: []

tags:
  - name: OpenAI Compatibility
    description: OpenAI-compatible completion and chat completion endpoints 
"""

WITHOUT_OPENAI = """
openapi: 3.1.1
info:
  title: {pipeline_name}
  description: |
    The Wallaroo Inference API allows you to perform real-time inference on deployed machine learning models and pipelines.
    
    ## Supported Data Formats
    
    The API supports multiple input and output formats:
    - **Pandas Records**: JSON format compatible with pandas DataFrame.to_json(orient="records")
    - **Apache Arrow**: Binary format for high-performance data exchange
    
    ## Authentication
    
    All requests require authentication using Bearer tokens obtained through the Wallaroo platform.
    
  version: {version}

servers:
  - url: {url}
    description: Wallaroo API

paths:
  /:
    post:
      summary: Perform inference on a deployed pipeline
      description: |
        Performs inference on a deployed pipeline. The pipeline processes data sequentially
        through a series of steps, where each step's output becomes the input for the next step.
        The final output represents the result of the entire pipeline's processing.
        
        The request body format and response format depend on the Content-Type header:
        - `application/json; format=pandas-records`: Pandas records format  
        - `application/vnd.apache.arrow.file`: Apache Arrow binary format
        
      operationId: runInference
      tags:
        - Native Inference
      parameters:
        - name: dataset[]
          in: query
          required: false
          description: |
            Dataset fields to include in response. Defaults to ["*"] which returns
            ["time", "in", "out", "anomaly", "metadata"].
          schema:
            type: array
            items:
              type: string
            default: ["*"]
          style: form
          explode: true
          example: ["time", "in", "out"]
        - name: dataset.exclude[]
          in: query
          required: false
          description: Dataset fields to exclude from response
          schema:
            type: array
            items:
              type: string
          style: form
          explode: true
          example: ["metadata"]
        - name: dataset.flatten
          in: query
          required: false
          description: |
            Determines whether to flatten nested dataset fields using dot notation.
          schema:
            type: boolean
            default: false
      requestBody:
        required: true
        content:
          application/json; format=pandas-records:
            description: Pandas records format (list of dictionaries)
            schema:
              $ref: '#/components/schemas/PandasRecordsInput'
          application/vnd.apache.arrow.file:
            description: Apache Arrow binary format
            schema:
              type: string
              format: binary
      responses:
        '200':
          description: Successful inference result
          content:
            application/json; format=pandas-records:
              description: Pandas records format response
              schema:
                $ref: '#/components/schemas/PandasRecordsOutput'
            application/vnd.apache.arrow.file:
              description: Apache Arrow binary format response
              schema:
                type: string
                format: binary
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '404':
          $ref: '#/components/responses/NotFound'
        '409':
          description: Pipeline type conflict
          content:
            application/json:
              description: Pandas records format response
              schema:
                $ref: '#/components/responses/Conflict'
              example:
                code: 409
                status: error
                error: "Inference failed. Please apply the appropriate OpenAI extensions to the inference endpoint. For additional help contact support@wallaroo.ai or your Wallaroo technical representative."
                source: engine
        '500':
          $ref: '#/components/responses/InternalServerError'
        '503':
          $ref: '#/components/responses/ServiceUnavailable'


components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: |
        Authentication token obtained through the Wallaroo platform.
        Use the SDK authentication methods to obtain a valid token.
        
  schemas:
    InferenceInputObject:
      type: object
      description: Object-based input for inference
      additionalProperties: true
      example:
        tensor: [1.0, 2.0, 3.0, 4.0]
        
    InferenceInputArray:
      type: array
      description: Array-based input for inference
      items:
        type: array
        items:
          type: number
      example:
        - [1.0, 2.0, 3.0]
        - [4.0, 5.0, 6.0]
        
    PandasRecordsInput:
      type: array
      items:
        type: object
        {input_schema}
    
    InferenceOutputObject:
      type: object
      description: Object-based output from inference
      additionalProperties: true
      example:
        prediction: [0.95, 0.05]
        confidence: 0.98
        
    InferenceOutputArray:
      type: array
      description: Array-based output from inference
      items:
        type: array
        items:
          type: number
      example:
        - [0.95, 0.05]
        - [0.87, 0.13]
        
    PandasRecordsOutput:
      type: array
      description: Pandas records output format
      items:
        oneOf:
        - type: object
          description: When flatten is `false`
          properties:
            time:
              type: integer
              format: int64
              description: Timestamp of the inference in milliseconds since epoch
              example: 1670564317817
            in:
              $ref: '#/components/schemas/PandasRecordsInput'
            out:
              type: object
              {output_schema}
            metadata:
              type: object
              properties:
                last_model:
                  type: object
                  properties:
                    model_name:
                      type: string
                    model_sha:
                      type: string
                pipeline_version:
                  type: string
                elapsed:
                  type: array
                  items:
                    type: integer
                    format: int64
                dropped:
                  type: array
                  items:
                    type: integer
                    format: int64
                partition:
                  type: string
            anomaly:
              type: object
              properties:
                count:
                  type: integer
                  format: int64
          required:
            - time
        - type: Object
          description: When flatten is `true`
          properties:
            time:
              type: integer
              format: int64
              description: Timestamp of the inference in milliseconds since epoch
              example: 1670564317817
            metadata.last_model:
              type: object
              properties:
                model_name:
                  type: string
                model_sha:
                  type: string
            metadata.pipeline_version:
              type: string
            metadata.elapsed:
              type: array
              items:
                type: integer
                format: int64
            metadata.dropped:
              type: array
              items:
                type: integer
                format: int64
            metadata.partition:
              type: string
            anomaly.count:
              type: integer
              format: int64
            {flattened_input_schema}
            {flattened_output_schema}


    ErrorResponse:
      type: object
      properties:
        code:
          type: integer
          description: HTTP status code
          example: 400
        status:
          type: string
          description: Error status message
          example: "error"
        error:
          type: string
          description: Detailed error message
          example: "Invalid input format"
        source:
          type: string
          description: Source of the error (e.g., engine, sidekick)
          example: "engine"
      required:
        - code
        - error
        
  responses:
    BadRequest:
      description: Invalid request format or parameters
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
          examples:
            invalid_tensor:
              summary: Invalid tensor format
              value:
                code: 400
                status: "error"
                error: "tensor values may not be null"
                source: "engine"
                
    Unauthorized:
      description: Authentication required or invalid
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
          example:
            code: 401
            status: "error"
            error: "Jwt is missing"
            source: "platform"
            
    NotFound:
      description: Deployment or pipeline not found
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
          example:
            code: 404
            status: "error"
            error: "Deployment not found"
            source: "platform"
            
    Conflict:
      description: Endpoint doesn't match pipeline type
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'

    InternalServerError:
      description: Internal server error
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
          example:
            code: 500
            status: "error"
            error: "Internal processing error"
            source: "engine"
            
    ServiceUnavailable:
      description: Service temporarily unavailable or insufficient resources
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
          examples:
            pipeline_being_activated:
              summary: Pipeline being activated
              value:
                code: 503
                status: "error"
                error: "The resources required to run this request are not available. Please check the inference endpoint status and try again"
                source: "engine"

security:
  - BearerAuth: []

tags:
  - name: Native Inference
    description: Wallaroo's native inference API with multiple data format support
"""

DEFAULT_SCHEMA = "additionalProperties: true"


class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True


def _base_openapi_for_arrow_dtype(t):
    if (
        pa.types.is_int8(t)
        or pa.types.is_int16(t)
        or pa.types.is_int32(t)
        or pa.types.is_uint8(t)
        or pa.types.is_uint16(t)
        or pa.types.is_uint32(t)
    ):
        return {"type": "integer", "format": "int32"}
    if pa.types.is_int64(t):
        return {"type": "integer", "format": "int64"}
    if hasattr(pa.types, "is_float16") and pa.types.is_float16(
        t
    ):  # older pyarrow may lack this
        return {"type": "number", "format": "float"}
    if pa.types.is_float32(t):
        return {"type": "number", "format": "float"}
    if pa.types.is_float64(t):
        return {"type": "number", "format": "double"}
    if pa.types.is_boolean(t):
        return {"type": "boolean"}
    if pa.types.is_string(t):
        return {"type": "string"}
    if pa.types.is_binary(t) or pa.types.is_large_binary(t):
        return {"type": "string", "format": "byte"}
    if pa.types.is_timestamp(t):
        return {"type": "string", "format": "date-time"}
    if pa.types.is_date32(t) or pa.types.is_date64(t):
        return {"type": "string", "format": "date"}
    return {"type": "string"}


def _fixed_shape_array(base_schema, shape):
    inner = base_schema
    for size in reversed(shape):
        inner = {
            "type": "array",
            "items": inner,
            "minItems": int(size),
            "maxItems": int(size),
        }
    return inner


def _try_parse_fixed_tensor_from_str(trepr: str):
    # e.g. "extension<arrow.fixed_shape_tensor[value_type=int64, shape=[3,32,32]]>"
    m = re.search(
        r"fixed_shape_tensor\[value_type=([^,\]]+),\s*shape=\[([0-9,\s]+)\]\]", trepr
    )
    if not m:
        return None, None
    vtype_s = m.group(1).strip()
    shape = [int(x) for x in m.group(2).replace(" ", "").split(",") if x]
    # map a few common dtype strings
    vt = {
        "int64": pa.int64(),
        "int32": pa.int32(),
        "float32": pa.float32(),
        "float64": pa.float64(),
        "float": pa.float32(),
        "double": pa.float64(),
    }.get(vtype_s, None)
    return vt, shape


def arrow_field_to_openapi(t):
    # ---- Handle ExtensionType even on old pyarrow
    if isinstance(t, pa.lib.ExtensionType) or hasattr(t, "storage_type"):
        ext_name = getattr(t, "extension_name", None)
        # Special-case fixed_shape_tensor
        if ext_name and "fixed_shape_tensor" in ext_name:
            value_t = getattr(t, "value_type", None)
            shape = list(getattr(t, "shape", []) or [])
            if not (value_t and shape):
                # try to parse from str() if attributes missing
                vt2, shape2 = _try_parse_fixed_tensor_from_str(str(t))
                value_t = value_t or vt2
                shape = shape or (shape2 or [])
            base = _base_openapi_for_arrow_dtype(
                value_t or getattr(t, "storage_type", pa.int32())
            )
            schema = (
                _fixed_shape_array(base, shape)
                if shape
                else _base_openapi_for_arrow_dtype(value_t)
            )
            schema = schema or {"type": "string"}
            schema["x-arrow-extension"] = {
                "name": ext_name,
                "dtype": str(value_t) if value_t else None,
                "shape": shape or None,
            }
            return schema
        # Unknown extension: map storage_type recursively, keep name
        storage = getattr(t, "storage_type", None)
        mapped = (
            arrow_field_to_openapi(storage)
            if storage is not None
            else {"type": "string"}
        )
        mapped.setdefault("x-arrow-extension", {})["name"] = (
            ext_name or "unknown-extension"
        )
        return mapped

    # ---- Map / object
    if hasattr(pa.types, "is_map") and pa.types.is_map(t):
        key_t, val_t = t.key_type, t.item_type
        schema = {
            "type": "object",
            "additionalProperties": arrow_field_to_openapi(val_t),
        }
        if not pa.types.is_string(key_t):
            schema["x-nonstring-map-key"] = str(key_t)
        return schema

    # ---- Lists
    if pa.types.is_list(t) or pa.types.is_large_list(t):
        return {"type": "array", "items": arrow_field_to_openapi(t.value_type)}

    # ---- FixedSizeList
    if pa.types.is_fixed_size_list(t):
        return {
            "type": "array",
            "items": arrow_field_to_openapi(t.value_type),
            "minItems": t.list_size,
            "maxItems": t.list_size,
        }

    # ---- Struct
    if pa.types.is_struct(t):
        props, req = {}, []
        for child in t:  # child is Field
            props[child.name] = arrow_field_to_openapi(child.type)
            if not child.nullable:
                req.append(child.name)
        return {"type": "object", "properties": props, "required": req or []}

    # ---- Primitives
    return _base_openapi_for_arrow_dtype(t)


def decode_arrow_schema_from_base64(base64_schema: str) -> pa.Schema:
    """Decode a base64-encoded Arrow schema.

    Args:
        base64_schema: Base64-encoded serialized Arrow schema string

    Returns:
        PyArrow Schema object
    """
    schema_bytes = base64.b64decode(base64_schema)
    reader = pa.ipc.open_stream(pa.BufferReader(schema_bytes))
    return reader.schema


def arrow_schema_to_openapi_yaml(schema: pa.Schema, indent=0, prepend_props="") -> str:
    props, required = {}, []
    for field in schema:
        props[prepend_props + field.name] = arrow_field_to_openapi(field.type)
        if not field.nullable:
            required.append(field.name)

    if prepend_props == "":
        openapi_schema = {
            "properties": props,
            "required": required or [],
        }
        spec = yaml.dump(openapi_schema, Dumper=NoAliasDumper, sort_keys=False)
    else:
        spec = yaml.dump(props, Dumper=NoAliasDumper, sort_keys=False)

    return "\n".join(
        [
            (" " * indent if ix > 0 else "") + line
            for ix, line in enumerate(spec.splitlines())
        ]
    )
