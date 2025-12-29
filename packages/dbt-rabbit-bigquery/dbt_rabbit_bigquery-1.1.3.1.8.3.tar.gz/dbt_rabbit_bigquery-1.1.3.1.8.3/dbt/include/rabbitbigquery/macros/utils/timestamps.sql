{% macro rabbitbigquery__current_timestamp() -%}
  current_timestamp()
{%- endmacro %}

{% macro rabbitbigquery__snapshot_string_as_time(timestamp) -%}
    {%- set result = 'TIMESTAMP("' ~ timestamp ~ '")' -%}
    {{ return(result) }}
{%- endmacro %}

{% macro rabbitbigquery__current_timestamp_backcompat() -%}
  current_timestamp
{%- endmacro %}
