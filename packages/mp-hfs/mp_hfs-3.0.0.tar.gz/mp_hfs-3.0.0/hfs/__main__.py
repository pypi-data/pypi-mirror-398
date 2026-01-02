"""HFS Worker 入口"""
import argparse
import os
from .worker import Worker


def main():
    parser = argparse.ArgumentParser(prog='hfs', description='HFS Worker')
    parser.add_argument('--redis-url', default=os.getenv('HFS_REDIS_URL'))
    parser.add_argument('--space-id', default=os.getenv('HFS_SPACE_ID'))
    parser.add_argument('--project-id', default=os.getenv('HFS_PROJECT_ID'))
    parser.add_argument('--node-id', default=os.getenv('HFS_NODE_ID'))
    args = parser.parse_args()

    if not args.redis_url or not args.space_id:
        parser.error('--redis-url and --space-id required')

    worker = Worker(
        redis_url=args.redis_url,
        space_id=args.space_id,
        project_id=args.project_id,
        node_id=args.node_id
    )
    worker.run()


if __name__ == '__main__':
    main()
