{% macro rabbitbigquery__scalar_function_create_replace_signature_sql(target_relation) %}
    CREATE OR REPLACE FUNCTION {{ target_relation.render() }} ({{ formatted_scalar_function_args_sql()}})
    RETURNS {{ model.returns.data_type }}
    {{ scalar_function_volatility_sql() }}
    AS
{% endmacro %}

{% macro rabbitbigquery__scalar_function_body_sql() %}
    (
       {{ model.compiled_code }}
    )
{% endmacro %}

{% macro rabbitbigquery__scalar_function_volatility_sql() %}
    {% set volatility = model.config.get('volatility') %}
    {% if volatility != None %}
        {% do unsupported_volatility_warning(volatility) %}
    {% endif %}
{% endmacro %}

{% macro rabbitbigquery__scalar_function_create_replace_signature_python(target_relation) %}
    CREATE OR REPLACE FUNCTION {{ target_relation.render() }} ({{ formatted_scalar_function_args_sql()}})
    RETURNS {{ model.returns.data_type }}
    LANGUAGE python
    OPTIONS(runtime_version = "{{ 'python-' ~ model.config.get('runtime_version') }}", entry_point = "{{ model.config.get('entry_point') }}")
    {{ scalar_function_volatility_sql() }}
    AS
{% endmacro %}

{% macro rabbitbigquery__get_scalar_function_body_python() %}
    r'''
{{ model.compiled_code }}
    '''
{% endmacro %}

{% macro rabbitbigquery__scalar_function_python(target_relation) %}
    {{ rabbitbigquery__scalar_function_create_replace_signature_python(target_relation) }}
    {{ rabbitbigquery__get_scalar_function_body_python() }}
{% endmacro %}
