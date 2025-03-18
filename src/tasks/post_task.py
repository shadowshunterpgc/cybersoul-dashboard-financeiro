from crewai import Task


class PostTasks:

    def post_blogger_task(self, agent):
        return Task(
            description="Escreve um post para o Blogger",
            expected_output="Uma postagem bem estruturada e coerente",
            agent=agent
        )

    def post_linkedin_task(self, agent):
        return Task(
            description="Write a post about the last news of Artificial Intelligence",
            expected_output="A text with maximum 15 lines, with a title, a subtitle and a link",
            agent=agent
        )