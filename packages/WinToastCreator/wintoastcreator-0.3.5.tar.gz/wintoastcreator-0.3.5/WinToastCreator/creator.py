from asyncio import sleep, get_running_loop, run, wait, FIRST_COMPLETED, Future
from pathlib import Path
from winrt.windows.data.xml.dom import XmlDocument
from winrt.windows.foundation import IPropertyValue, Uri
from winrt.windows.ui.notifications import ToastNotificationManager, ToastNotification, NotificationData, ToastActivatedEventArgs, ToastDismissedEventArgs, ToastFailedEventArgs
from winrt.windows.media.ocr import OcrEngine
from winrt.windows.media.playback import MediaPlayer
from winrt.windows.media.core import MediaSource
from winrt.windows.storage import StorageFile, FileAccessMode
from winrt.windows.media.speechsynthesis import SpeechSynthesizer
from winrt.windows.graphics.imaging import BitmapDecoder
from winrt.windows.globalization import Language

DEFAULT_APP_ID = 'Python'

xml = """<toast activationType="protocol" launch="http:" scenario="{scenario}">
    <visual>
        <binding template="ToastGeneric"></binding>
    </visual>
</toast>"""

def set_attribute(document, xpath, name, value):
    attr = document.create_attribute(name)
    attr.value = value
    document.select_single_node(xpath).attributes.set_named_item(attr)

def add_text(msg, document):
    msg = {'text': msg} if isinstance(msg, str) else msg
    text = document.create_element('text')
    for k, v in msg.items():
        text.inner_text = v if k == 'text' else text.set_attribute(k, v)
    document.select_single_node('//binding').append_child(text)

def add_icon(icon, document):
    if isinstance(icon, str):
        icon = {'placement': 'appLogoOverride', 'hint-crop': 'circle', 'src': icon}
    img = document.create_element('image')
    for k, v in icon.items():
        img.set_attribute(k, v)
    document.select_single_node('//binding').append_child(img)

def add_image(img, document):
    if isinstance(img, str):
        img = {'src': img}
    img_el = document.create_element('image')
    for k, v in img.items():
        img_el.set_attribute(k, v)
    document.select_single_node('//binding').append_child(img_el)

def add_progress(prog, document):
    prog_el = document.create_element('progress')
    for name in prog:
        prog_el.set_attribute(name, '{' + name + '}')
    document.select_single_node('//binding').append_child(prog_el)

def add_audio(aud, document):
    if isinstance(aud, str): 
        aud = {'src': aud}
    audio = document.create_element('audio')
    [audio.set_attribute(k, v) for k, v in aud.items()]
    toast_element = document.select_single_node('toast')
    toast_element and toast_element.append_child(audio)

def create_actions(document):
    toast = document.select_single_node('/toast')
    actions = document.create_element('actions')
    toast.append_child(actions)
    return actions

def add_button(button, document):
    if isinstance(button, str):
        button = {'activationType': 'protocol', 'arguments': 'http:' + button, 'content': button}
    actions = (document.select_single_node('//actions') or create_actions(document))
    action = document.create_element('action')
    for k, v in button.items():
        action.set_attribute(k, v)
    actions.append_child(action)

def add_input(id, document):
    if isinstance(id, str):
        id = {'id': id, 'type': 'text', 'placeHolderContent': id}
    actions = (document.select_single_node('//actions') or create_actions(document))
    input_el = document.create_element('input')
    for k, v in id.items():
        input_el.set_attribute(k, v)
    actions.append_child(input_el)

def add_selection(selection, document):
    if isinstance(selection, list):
        selection = {'input': {'id': 'selection', 'type': 'selection'}, 'selection': selection}
    actions = document.select_single_node('//actions') or create_actions(document)
    input_el = document.create_element('input')
    
    for k, v in selection['input'].items():
        input_el.set_attribute(k, v)
    actions.append_child(input_el)
    
    for item in selection['selection']:
        item = dict(id=item, content=item) if not isinstance(item, dict) else item
        sel_el = document.create_element('selection')
        [sel_el.set_attribute(k, v) for k, v in item.items()]
        input_el.append_child(sel_el)

def result_wrapper(*args):
    global result
    result = args
    return result

def activated_args(_, event):
    e = ToastActivatedEventArgs._from(event)
    user_input = {}
    for name in e.user_input:
        value = IPropertyValue._from(e.user_input[name]).get_string()
        user_input[name] = value
    return {'arguments': e.arguments, 'user_input': user_input}

async def play_sound(audio):
    source = (MediaSource.create_from_uri(Uri(audio))
              if audio.startswith('http')
              else MediaSource.create_from_storage_file(await StorageFile.get_file_from_path_async(audio)))
    player = MediaPlayer()
    player.source = source
    player.play()
    await sleep(7)

async def speak(text):
    stream = await SpeechSynthesizer().synthesize_text_to_stream_async(text)
    player = MediaPlayer()
    player.source = MediaSource.create_from_stream(stream, stream.content_type)
    player.play()
    await sleep(7)

async def recognize(ocr):
    if isinstance(ocr, str):
        ocr = {'ocr': ocr}

    file = await StorageFile.get_file_from_path_async(ocr['ocr'])
    stream = await file.open_async(FileAccessMode.READ)

    decoder = await BitmapDecoder.create_async(stream)
    bitmap = await decoder.get_software_bitmap_async()

    lang = ocr.get('lang')
    if lang and OcrEngine.is_language_supported(Language(lang)):
        engine = OcrEngine.try_create_from_language(Language(lang))
    else:
        engine = OcrEngine.try_create_from_user_profile_languages()

    result = await engine.recognize_async(bitmap)
    
    return {"text": result.text, "lines": [line.text for line in result.lines], "word_count": len(result.lines) if result.lines else 0}

def available_recognizer_languages():
    for language in OcrEngine.available_recognizer_languages:
        print(language.display_name + ':',  language.language_tag)
    print('\nGet-WindowsCapability -Online | Where-Object { $_.Name -like "Language.OCR*" }\nAdd-WindowsCapability -Online -Name Language.OCR~~~ru-RU~0.0.1.0')

def notify(title=None, body=None, on_click=print, icon=None, image=None, progress=None, audio=None,
           dialogue=None, duration=None, input=None, inputs=[], selection=None, selections=[],
           button=None, buttons=[], xml=xml, app_id=DEFAULT_APP_ID, scenario=None, tag=None, group=None):
    doc = XmlDocument()
    doc.load_xml(xml.format(scenario=scenario or 'default'))

    if isinstance(on_click, str):
        set_attribute(doc, '/toast', 'launch', on_click)
    if duration:
        set_attribute(doc, '/toast', 'duration', duration)

    for text in ([title] if title else []) + ([body] if body else []):
        add_text(text, doc)
    for item in inputs + ([input] if input else []):
        add_input(item, doc)
    for sel in selections + ([selection] if selection else []):
        add_selection(sel, doc)
    for btn in buttons + ([button] if button else []):
        add_button(btn, doc)

    if icon: 
        add_icon(icon, doc)
    if image: 
        add_image(image, doc)
    if progress: 
        add_progress(progress, doc)

    if audio:
        if isinstance(audio, str) and audio.startswith('ms'):
            add_audio(audio, doc)
        elif isinstance(audio, str) and Path(audio).is_file():
            add_audio(f'file:///{Path(audio).absolute().as_posix()}', doc)
        elif isinstance(audio, dict) and 'src' in audio and audio['src'].startswith('ms'):
            add_audio(audio, doc)
        else:
            add_audio({'silent': 'true'}, doc)
    elif dialogue:
        add_audio({'silent': 'true'}, doc)

    notification = ToastNotification(doc)
    
    if progress:
        data = NotificationData()
        data.values.update({k: str(v) for k, v in progress.items()})
        data.sequence_number = 1
        notification.data, notification.tag = data, 'my_tag'
    
    if tag: 
        notification.tag = tag
    if group: 
        notification.group = group

    try:
        notifier = (ToastNotificationManager.create_toast_notifier() if app_id == DEFAULT_APP_ID else ToastNotificationManager.create_toast_notifier_with_id(app_id))
    except Exception:
        notifier = ToastNotificationManager.create_toast_notifier_with_id(app_id)

    notifier.show(notification)
    return notification

async def toast_async(title=None, body=None, on_click=print, icon=None, image=None, progress=None, audio=None, dialogue=None,
            duration=None, input=None, inputs=[], selection=None, selections=[], button=None, buttons=[], xml=xml, app_id=DEFAULT_APP_ID, 
            ocr=None, on_dismissed=print, on_failed=print, scenario=None, tag=None, group=None, timeout=30.0):
    if ocr:
        title = 'Результат OCR'
        result = await recognize(ocr)
        body = result.get('text', 'Не удалось распознать текст')
        if isinstance(ocr, str):
            src = ocr
        else:
            src = ocr.get('ocr', '')
        image = {'placement': 'hero', 'src': src}
    
    notification = notify(title, body, on_click, icon, image, progress, audio, dialogue, duration, input, inputs, 
            selection, selections, button, buttons, xml, app_id, scenario, tag, group)
    
    loop = get_running_loop()
    futures, tokens = [], {}
    
    if audio and isinstance(audio, str) and not audio.startswith('ms'):
        futures.append(loop.create_task(play_sound(audio)))
    if dialogue:
        futures.append(loop.create_task(speak(dialogue)))
    
    def handle(evt, cb):
        future = loop.create_future()
        token = getattr(notification, f'add_{evt}')(lambda *a: loop.call_soon_threadsafe(future.set_result, cb(*a)))
        futures.append(future)
        tokens[evt] = token
        return future
    
    handle('activated', lambda *a: on_click(activated_args(*a)))
    handle('dismissed', lambda _, e: on_dismissed(result_wrapper(ToastDismissedEventArgs._from(e).reason)))
    handle('failed', lambda _, e: on_failed(result_wrapper(ToastFailedEventArgs._from(e).error_code)))
    
    try:
        done, pending = await wait(futures, timeout=timeout, return_when=FIRST_COMPLETED)
        for task in pending: task.cancel()
    finally:
        for evt, token in tokens.items(): 
            getattr(notification, f'remove_{evt}')(token)

def toast(*args, **kwargs):
    coro = toast_async(*args, **kwargs)
    try:
        loop = get_running_loop()
    except RuntimeError:
        return run(coro)
    future = Future()
    loop.create_task(coro).add_done_callback(lambda t: future.set_exception(t.exception()) if t.exception() else future.set_result(t.result()))
    return future

async def atoast(*args, **kwargs):
    return await toast_async(*args, **kwargs)

def update_progress(progress, app_id=DEFAULT_APP_ID, tag='my_tag'):
    data = NotificationData()
    for name, value in progress.items():
        data.values[name] = str(value)
    data.sequence_number = 2
    if app_id == DEFAULT_APP_ID:
        try:
            notifier = ToastNotificationManager.create_toast_notifier()
        except Exception as e:
            notifier = ToastNotificationManager.create_toast_notifier(app_id)
    else:
        notifier = ToastNotificationManager.create_toast_notifier(app_id)
    return notifier.show(data, tag)

def clear_toast(app_id=DEFAULT_APP_ID, tag=None, group=None):
    history = ToastNotificationManager.history
    if tag and not group:
        raise AttributeError('для удаления уведомления необходимо указать значение группы')
    if not tag and not group:
        history.clear(app_id)
    elif tag and group:
        history.remove(tag, group, app_id)
    else:
        history.remove_group(group, app_id)