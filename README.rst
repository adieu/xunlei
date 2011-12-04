API Usage
=========

Create a Xunlei object::

    import xunlei
    xunlei_obj = xunlei.Xunlei(USERNAME, PASSWORD, COOKIE_FILE_PATH)

List Xunlei lixian tasks::

    items = xunlei_obj.dashboard()

List a bittorrent task::

    items = xunlei_obj.list_bt(url, task_id) # url and task_id are from dashboard() function

Download a task::

    xunlei_obj.dowload(url, filename)

Download a task with file size checking and resume::

    xunlei_obj.smart_download(url, filename, size)


CLI Usage
=========

Edit config file at ``~/xunleirc``, add settings for ``username`` and ``password``

List xunlei tasks::

    xunlei_cli dashboard

Download a task::

    xunlei_cli download TASK_ID

