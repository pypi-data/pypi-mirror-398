{% macro rabbitbigquery__date_trunc(datepart, date) -%}
    timestamp_trunc(
        cast({{date}} as timestamp),
        {{datepart}}
    )

{%- endmacro %}
