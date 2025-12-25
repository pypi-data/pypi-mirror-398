{% extends "base_page.html" %}
{% load static wagtailcore_tags %}

{% block title %}{% if page.seo_title %}{% endif %}{% endblock %}

{% block content %}
<div class="container mx-auto px-4 py-8">
    <div class="max-w-4xl mx-auto">
        <h1 class="text-4xl font-bold text-gray-900 mb-6">
            {{ page.title }}
        </h1>
        
        {% if page.introduction %}
        <div class="text-xl text-gray-600 mb-8">
            {{ page.introduction|linebreaks }}
        </div>
        {% endif %}
        
        {% if page.body %}
        <div class="prose prose-lg max-w-none">
            {% for block in page.body %}
                {% include_block block %}
            {% endfor %}
        </div>
        {% endif %}
    </div>
</div>
{% endblock %}
