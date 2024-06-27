DEFAULT_VALUES = ["Tone of email: Casual", "Style of email: Concice", "Length of email: Short", "Complexity of email: Simple"]  # Stores additional options selected by the user
PROMPT_INFO = "When you generate an email, please keep in mind the format that I want the result back in. The first line should have Subject: [insert subject here] followed by an empty line and then the email. When ending the email also have an empty line before the closing statement for example, an empty line before Best, [Your Name]"
ROLE_VALUES = {
    "Sales Executive": "You are responsible for identifying and closing sales opportunities, building customer relationships, and achieving sales targets.",
    "Software Engineer": "You design, develop, and maintain software applications, ensuring they meet user needs and technical requirements.",
    "Product Manager": "You oversee the development and delivery of products, coordinating between different teams and ensuring the product meets market needs.",
    "Customer Support Specialist": "You assist customers by addressing their inquiries, resolving issues, and providing information about products and services.",
    "Marketing Manager": "You develop and implement marketing strategies to promote products or services, increase brand awareness, and drive sales.",
    "Human Resources Manager": "You manage employee relations, recruitment, performance management, and ensure compliance with labor laws.",
    "Finance Analyst": "You analyze financial data, prepare reports, and provide insights to support decision-making and financial planning.",
    "Operations Manager": "You oversee the day-to-day operations of the company, ensuring efficiency, productivity, and adherence to organizational policies.",
    "Data Scientist": "You analyze and interpret complex data to provide insights, develop predictive models, and support data-driven decision-making.",
    "Graphic Designer": "You create visual content for various media, including websites, advertisements, and publications, ensuring it aligns with brand guidelines.",
    "Other": "Role Summary",
}
REGEN_TITLE = "For the following generated email, youi must generate a new title. The previously generated title will be attatched to the email but when you generate a new title, make sure it is unique and different than the one provided. For your response, format it as you normally would. Include Subject: followed by the newly generated title. You dont need to return any other content other than that.\n\n"
PRECON = "The reason for this message is to give context, you only need to reply to this message with \"Ok\". The following message with contain the actual prompt in which you will use these details above to generate an email. "
META_SPECIAL = """Dont add any extra details at the start of the message. Also for readability, feel free to add empty lines between text.

For example, if the theme is to say hi to my boss, it would be formatted as such:

Subject: Test Email

Hi boss, hope you are having a good day!

Best,
[Your Name]

"""
parameterized_prompt = """
Your role in writing the email: [roleplay]

Email Theme/Summary: [Theme/Summary]
Email Notes: [Notes]
Email Keywords: [Keywords]

Email Tone: [Tone]
Email Style: [Style]
Email Length: [Length]
Email Complexity: [Complexity]
"""
