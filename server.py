from asyncio import to_thread
from aiosonic import HTTPClient
from aiohttp.web import Application, RouteTableDef, Request, Response, FileResponse, run_app
from os import path, makedirs

remote_host = 'https://www.remote-host.com'     #Replace with your remote host URL
cwd = path.dirname(__file__)
my_app = Application()
routes = RouteTableDef()

async def get_it(url: str) -> bytes:
    '''
    Performs a remote GET request.

    Parameters
    ----------
    url: str
        The remote URL to perform the GET request on

    Returns
    -------
    bytes
        The remote GET response
    '''
    async with HTTPClient() as client:
        response = await client.get(url)
        data = await response.content()
        return data

async def post_it(url: str, params: dict) -> bytes:
    '''
    Performs a remote POST request.

    Parameters
    ----------
    url: str
        The remote URL to POST
    params: dict
        The local POST request parameters

    Returns
    -------
    bytes
        The remote POST response
    '''
    async with HTTPClient() as client:
        response = await client.post(url=url, data=params)
        data = await response.content()
        return data

def save_file(full_path: str, content: bytes) -> None:
    '''
    Saves the remote file locally.

    Parameters
    ----------
    full_path: str
        The full local path to store the file
    content: bytes
        The file content
    '''
    #Create the necessary folders to save the file if it does not exist
    makedirs(path.dirname(full_path), exist_ok=True)
    with open(full_path, 'wb') as file:
        file.write(content)

@routes.get('/{name:.*}')
async def get_handler(request: Request) -> FileResponse:
    '''
    Handles basic GET requests to the remote host.

    Parameters
    ----------
    request : Request
        The local GET request
        
    Returns
    -------
    FileResponse
        The remote GET response
    '''
    rel_path = ((str(request.rel_url)).split('?'))[0]   #Remove query strings before serving files
    full_path = cwd + rel_path
    #If local file is present, serve that,
    #else download the file from the remote host first
    if not path.exists(full_path):                     
        await local_folder(rel_path, full_path)
    return FileResponse(full_path)

@routes.post('/{name:.*}')
async def post_handler(request: Request) -> Response:
    '''
    Handles basic POST requests to the remote host.

    Parameters
    ----------
    request : Request
        The local POST request

    Returns
    -------
    Response
        The remote POST response
    '''
    rel_path = str(request.rel_url)
    params = dict(await request.post())
    data = await post_it(f"{remote_host}{rel_path}", params)
    return Response(body=data)

async def local_folder(rel_path: str, full_path: str) -> None:
    '''
    Retrieves and stores the remote file locally.

    Parameters
    ----------
    rel_path : str
        The web request's relative path
    full_path : str
        The full local path to store the file
    '''
    async with HTTPClient() as client:
        try:
            page_response = (await client.get(f"{remote_host}{rel_path}")).content()
            response = await page_response
            #Asynchronously save file content in a different thread to prevent file I/O blocking
            await to_thread(save_file, full_path, response)                  
        except Exception as e:
            print("Uh oh, something went wrong : ", e)

def main(host: str = '127.0.0.1', port: int = 80) -> None:
    '''
    Runs the web server.

    Parameters
    ----------
    host : str
        The localhost address to run the web server on
        Defaults to 127.0.0.1 if not supplied
    port : int
        The port to run the web server on
        Defaults to 80 if not supplied
    '''
    my_app.add_routes(routes)
    run_app(my_app, host=host, port=port)

if __name__ == '__main__':
    main()
