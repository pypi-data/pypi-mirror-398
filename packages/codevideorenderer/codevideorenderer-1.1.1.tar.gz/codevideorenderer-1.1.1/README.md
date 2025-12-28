If you encounter any issues, please send an email to [my email](mailto:zhuchongjing_pypi@163.com). We welcome bug feedback, and we will fix them as soon as possible.

This library is used to generate videos of input code, with the camera following the cursor movement.

Command Line Installation:

```bash
pip install CodeVideoRenderer
```

**Example**

```python
from CodeVideoRenderer import *
video = CameraFollowCursorCV(code_string="print('Hello World!')", language='python')
video.render()
```

For more information: [CodeVideoRenderer on GitHub](https://github.com/ZhuChongjing/CodeVideoRenderer)




