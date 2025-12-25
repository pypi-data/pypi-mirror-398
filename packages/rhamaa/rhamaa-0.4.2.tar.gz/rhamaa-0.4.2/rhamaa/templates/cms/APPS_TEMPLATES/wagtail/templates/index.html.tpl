{% extends "base.html" %}
{% load static %}

{% block title %}{{app_verbose_name}}{% endblock %}

{% block content %}
<div class="container mx-auto px-4 py-8">
    <div class="max-w-4xl mx-auto">
        <h1 class="text-4xl font-bold text-gray-900 mb-6">
            {{ title }}
        </h1>
        
        <div class="bg-white rounded-lg shadow-md p-6 mb-8">
            <h2 class="text-2xl font-semibold text-gray-800 mb-4">
                Welcome to {{ app_name }} App
            </h2>
            
            <p class="text-gray-600 mb-4">
                This is a starter template for your new RhamaaCMS app. 
                You can customize this template and add your own content.
            </p>
            
            <div class="bg-blue-50 border-l-4 border-blue-400 p-4 mb-4">
                <div class="flex">
                    <div class="ml-3">
                        <p class="text-sm text-blue-700">
                            <strong>Next Steps:</strong>
                        </p>
                        <ul class="text-sm text-blue-600 mt-2 list-disc list-inside">
                            <li>Customize your models in <code>models.py</code></li>
                            <li>Add your views in <code>views.py</code></li>
                            <li>Update this template in <code>templates/{{app_name}}/index.html</code></li>
                            <li>Add your static files in <code>static/</code> directory</li>
                        </ul>
                    </div>
                </div>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
                <div class="bg-gray-50 p-4 rounded-lg">
                    <h3 class="font-semibold text-gray-800 mb-2">Models</h3>
                    <p class="text-sm text-gray-600">
                        Define your data models in <code>models.py</code>
                    </p>
                </div>
                
                <div class="bg-gray-50 p-4 rounded-lg">
                    <h3 class="font-semibold text-gray-800 mb-2">Views</h3>
                    <p class="text-sm text-gray-600">
                        Create your view functions in <code>views.py</code>
                    </p>
                </div>
                
                <div class="bg-gray-50 p-4 rounded-lg">
                    <h3 class="font-semibold text-gray-800 mb-2">Templates</h3>
                    <p class="text-sm text-gray-600">
                        Design your HTML templates in <code>templates/</code>
                    </p>
                </div>
                
                <div class="bg-gray-50 p-4 rounded-lg">
                    <h3 class="font-semibold text-gray-800 mb-2">Static Files</h3>
                    <p class="text-sm text-gray-600">
                        Add CSS, JS, and images in <code>static/</code>
                    </p>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
