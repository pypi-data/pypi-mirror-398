
from pygeai.core.base.responses import ErrorListResponse
from pygeai.lab.managers import AILabManager
from pygeai.lab.models import KnowledgeBase


def main():
    manager = AILabManager()

    # Step 1: Create a Knowledge Base
    print("=== Creating Knowledge Base ===")
    kb = KnowledgeBase(
        name="TestKnowledgeBase2",
        artifact_type_name=["Document"],
    )
    artifacts = ["artifact1", "artifact2"]
    metadata = ["tag1", "tag2"]
    # create_result = manager.create_knowledge_base(project_id, kb, artifacts, metadata)
    create_result = manager.create_knowledge_base(kb)

    if isinstance(create_result, ErrorListResponse):
        print(f"Error creating knowledge base: {create_result}")
        return
    else:
        print(f"Created knowledge base: {create_result.name} (ID: {create_result.id})")
        created_kb = create_result

    # Step 2: List Knowledge Bases
    print("\n=== Listing Knowledge Bases ===")
    list_result = manager.list_knowledge_bases(name=None, start=0, count=10)

    if isinstance(list_result, ErrorListResponse):
        print(f"Error listing knowledge bases: {list_result}")
    else:
        print(f"Found {len(list_result)} knowledge bases:")
        for kb in list_result:
            print(f"- {kb.name} (ID: {kb.id}, Artifact Type: {kb.artifact_type_name})")

    # Step 3: Get Knowledge Base by Name
    print("\n=== Getting Knowledge Base by Name ===")
    get_result = manager.get_knowledge_base(kb_name=created_kb.name)

    if isinstance(get_result, ErrorListResponse):
        print(f"Error getting knowledge base: {get_result}")
    else:
        print(f"Retrieved knowledge base: {get_result.name} (ID: {get_result.id})")

    # Step 4: Get Knowledge Base by ID
    print("\n=== Getting Knowledge Base by ID ===")
    get_result_by_id = manager.get_knowledge_base(kb_id=created_kb.id)

    if isinstance(get_result_by_id, ErrorListResponse):
        print(f"Error getting knowledge base by ID: {get_result_by_id}")
    else:
        print(f"Retrieved knowledge base by ID: {get_result_by_id.name} (ID: {get_result_by_id.id})")

    # Step 5: Delete Knowledge Base
    print("\n=== Deleting Knowledge Base ===")
    delete_result = manager.delete_knowledge_base(kb_id=created_kb.id)

    if isinstance(delete_result, ErrorListResponse):
        print(f"Error deleting knowledge base: {delete_result}")
    else:
        print("Knowledge base deleted successfully")


if __name__ == "__main__":
    try:
        main()
    except ValueError as e:
        print(f"ValueError: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")