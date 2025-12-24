import sys

from miriel import Miriel


def non_changing_tests(miriel_client):
    # Example usage of the Miriel client
    user_response = miriel_client.get_users()
    print(f'User response: {user_response}')
    user_id = user_response['users'][0]

    query_response = miriel_client.query('What is this document about?', user_id)
    print(f'Query response: {query_response}')

    query_response = miriel_client.query(
        'What is this picture of?',
        user_id,
        input_images=[
            'https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg'
        ],
    )
    print(f'Query with image response: {query_response}')

    # graph_query_response = miriel_client.graph_query("What is the relationship between the documents?", user_id)
    # print(f"Graph query response: {graph_query_response}")

    get_docs_for_query_response = miriel_client.get_docs_for_query(
        'What is the relationship between the documents?', user_id
    )
    print(f'Get docs for query response: {get_docs_for_query_response}')

    get_monitor_sources_response = miriel_client.get_monitor_sources(user_id)
    print(f'Get monitor sources response: {get_monitor_sources_response}')


def changing_tests(miriel_client):
    user_response = miriel_client.get_users()
    print(f'User response: {user_response}')
    user_id = user_response['users'][0]

    # response = miriel_client.add_urls(user_id, ["https://beacon.miriel.ai/about"])
    # print(f"Add urls response: {response}")

    # response = miriel_client.add_image_as_document(user_id, "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg")
    response = miriel_client.add_image_as_document(
        user_id,
        'https://photographylife.com/cdn-cgi/imagedelivery/GrQZt6ZFhE4jsKqjDEtqRA/photographylife.com/2023/05/Nikon-Z8-Official-Samples-00021.jpg/w=640',
    )

    print(f'Add image as document response: {response}')

    # response = miriel_client.add_string_as_document(user_id, "This is a test document")
    # print(f"Add string as document response: {response}")


def main():
    if len(sys.argv) < 2:
        print('Please provide the API key as a command-line argument.')
        sys.exit(1)

    api_key = sys.argv[1]

    miriel_client = Miriel(api_key)
    # non_changing_tests(miriel_client)
    changing_tests(miriel_client)

    # user_response = miriel_client.get_users()
    # print(f"User response: {user_response}")
    # user_id = user_response['users'][0]

    # response = miriel_client.remove_all_documents(user_id)
    # print(f"Remove all documents response: {response}")


if __name__ == '__main__':
    main()
