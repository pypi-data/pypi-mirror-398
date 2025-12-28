import json
import subprocess
import datetime
import sys
import time

# import psycopg2
# from psycopg2.extras import Json
import click
import humanize
from rich.console import Console
from rich.table import Table, Column
from rich import inspect, box
from rich.pretty import pprint
from rich.panel import Panel


@click.command()
@click.option('-a', '--archive', default=str(datetime.date.today()), help='Substring archive match')
@click.option('-n', '--noop', is_flag=True, default=False, help="Don't actually do anything")
@click.option('-l', '--last', help='Look at <last> number of archives')
@click.option('-r', '--repo', help='Specific repo')
def main(archive, noop, last, repo):
    console = Console()
    # if not noop:
    #     conn = psycopg2.connect('dbname=borg user=borg host=db password=somepassword')
    #     cur = conn.cursor()

    # cmd = subprocess.run('/root/venv/borgmatic-master/bin/borgmatic -c /etc/borgmatic/config.yaml info --glob-archives *{}* --json'.format(archive).split(), capture_output=True, check=True)
    borgmatic_command = 'borgmatic --no-color info --json'
    borgmatic_command += f' --repo {repo}' if repo else ''
    borgmatic_command += f' --last {last}' if last else ''
    with console.status(f'Running {borgmatic_command}...', spinner='dots10'):
        try:
            cmd = subprocess.run(borgmatic_command.split(), capture_output=True, check=True)
        except subprocess.CalledProcessError as e:
            console.print(f'\n[bright_red]Error running borgmatic:')
            if e.stdout:
                console.rule('stdout')
                console.print(e.stdout.decode("utf-8"), highlight=False)
            if e.stderr:
                console.rule('stderr')
                console.print(e.stderr.decode("utf-8"), highlight=False)
            sys.exit(1)
    try:
        j = json.loads(cmd.stdout.decode('utf-8'))
        #        pprint(j)
        #        z = j[0].copy()
        #        del z['archives']

        #        for x in j[0]['archives']:
        #            temp = z.copy()
        #            temp.update({'archives': [x]})
        #            if not noop:
        #                cur.execute('INSERT INTO stats (data) VALUES (%s)', [Json(temp)])
        #            pprint(temp)

        if not j[0]['archives']:
            print('No archives in repo.')
            return

        table = Table(
            'Name',
            'Duration',
            'Start',
            'End',
            Column(header='Dedupe size', justify='right'),
            Column(header='Orig size', justify='right'),
            Column(header='Files', justify='right'),
            title='Backups',
            header_style='on grey19',
            box=box.MINIMAL_HEAVY_HEAD,
            title_style='reverse',
        )
        for result in j:
            for archive in result['archives']:
                if archive:
                    table.add_row(
                        archive['name'],
                        time.strftime('%H:%M:%S', time.gmtime(archive['duration'])),
                        archive['start'],
                        archive['end'],
                        humanize.naturalsize(archive['stats']['deduplicated_size']),
                        humanize.naturalsize(archive["stats"]["original_size"]),
                        archive["stats"]["nfiles"],
                    )

        console.print(table)

        # if not noop:
        #     conn.commit()
        #     cur.close()
        #     conn.close()

    except json.decoder.JSONDecodeError as e:
        print(f'Something is wrong with the JSON returned: {e}')
        print(f'This is the returned subprocess object: {cmd}')


if __name__ == '__main__':
    main()
