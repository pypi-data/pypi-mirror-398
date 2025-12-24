#!/usr/bin/env python3
"""
Tunnel System V3 CLI
Command: tunnel3
"""
import click
import asyncio
import sys

@click.group()
@click.option('--worker', '-w', envvar='TUNNEL3_WORKER_URL', help='Worker URL')
@click.pass_context
def cli(ctx, worker):
    """Tunnel System V3 CLI"""
    ctx.ensure_object(dict)
    ctx.obj['worker_url'] = worker or 'http://localhost:8787'

@cli.command()
@click.option('--id', 'node_id', help='Node ID (auto-generate if not specified)')
@click.option('--tag', '-t', multiple=True, help='Tags')
@click.option('--service', '-s', multiple=True, default=['exec'], help='Services to enable')
@click.pass_context
def agent(ctx, node_id, tag, service):
    """Start agent"""
    from agent.agent_v3 import Agent
    
    config = {
        'worker_url': ctx.obj['worker_url'],
        'node_id': node_id,
        'tags': list(tag),
        'services': [{'name': s, 'type': 'builtin'} for s in service]
    }
    
    agent = Agent(config)
    try:
        asyncio.run(agent.start())
    except KeyboardInterrupt:
        click.echo('\nAgent stopped')

@cli.command()
@click.argument('command')
@click.option('--node', '-n', help='Target node ID')
@click.option('--tag', '-t', multiple=True, help='Filter by tags')
@click.pass_context
def exec(ctx, command, node, tag):
    """Execute command on remote node"""
    import requests
    
    worker_url = ctx.obj['worker_url']
    payload = {'command': command}
    
    if node:
        payload['node'] = node
    elif tag:
        payload['tags'] = list(tag)
    
    try:
        resp = requests.post(f'{worker_url}/api/v1/exec', json=payload, timeout=30)
        if resp.status_code == 200:
            result = resp.json()
            click.echo(result.get('stdout', ''))
            if result.get('stderr'):
                click.echo(result['stderr'], err=True)
        else:
            click.echo(f"Error: {resp.text}", err=True)
            sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--status', type=click.Choice(['online', 'offline']), help='Filter by status')
@click.option('--tag', '-t', multiple=True, help='Filter by tags')
@click.pass_context
def nodes(ctx, status, tag):
    """List nodes"""
    import requests
    
    worker_url = ctx.obj['worker_url']
    params = {}
    if status:
        params['status'] = status
    if tag:
        params['tags'] = ','.join(tag)
    
    try:
        resp = requests.get(f'{worker_url}/api/v1/nodes', params=params)
        if resp.status_code == 200:
            data = resp.json()
            for node in data['nodes']:
                status_icon = '🟢' if node['status'] == 'online' else '🔴'
                tags_str = ','.join(node.get('tags', [])[:3])
                click.echo(f"{status_icon} {node['node_id']:20s} [{tags_str}]")
        else:
            click.echo(f"Error: {resp.text}", err=True)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

@cli.group()
def batch():
    """Batch operations"""
    pass

@batch.command('exec')
@click.argument('command')
@click.option('--tag', '-t', multiple=True, help='Target tags')
@click.option('--concurrency', '-c', default=10, help='Concurrent executions')
@click.pass_context
def batch_exec(ctx, command, tag, concurrency):
    """Execute command on multiple nodes"""
    import requests
    import time
    
    worker_url = ctx.obj['worker_url']
    
    payload = {
        'command': command,
        'targets': {'tags': list(tag)},
        'options': {'concurrency': concurrency}
    }
    
    try:
        # Submit task
        resp = requests.post(f'{worker_url}/api/v1/batch/exec', json=payload)
        if resp.status_code != 200:
            click.echo(f"Error: {resp.text}", err=True)
            return
        
        task = resp.json()
        task_id = task['taskId']
        click.echo(f"Task {task_id} started ({task['total']} nodes)")
        
        # Poll for results
        while True:
            time.sleep(2)
            status_resp = requests.get(f'{worker_url}/api/v1/batch/tasks/{task_id}')
            status = status_resp.json()
            
            click.echo(f"Progress: {status['completed']}/{status['total']}")
            
            if status['status'] in ['completed', 'failed']:
                break
        
        # Get results
        results_resp = requests.get(f'{worker_url}/api/v1/batch/tasks/{task_id}/results')
        results = results_resp.json()
        
        click.echo('\nResults:')
        for r in results['results']:
            icon = '✅' if r['status'] == 'success' else '❌'
            output = r.get('data', {}).get('stdout', r.get('error', ''))
            click.echo(f"{icon} {r['node_id']}: {output}")
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

if __name__ == '__main__':
    cli()
