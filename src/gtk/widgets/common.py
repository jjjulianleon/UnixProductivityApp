"""
Piezas de UI compartidas entre vistas.
"""
import gi
gi.require_version('Gtk', '4.0')

from gi.repository import GLib, Gtk


def empty_state(icon_name: str, title: str, subtitle: str = "") -> Gtk.Box:
    """Estado vacio compacto, para usar DENTRO de una tarjeta.

    Adw.StatusPage esta pensado para ocupar una vista entera: metido en una
    tarjeta dibuja un icono de 128px y un titulo enorme que se comen el hueco.
    Aqui el icono es de 32px y el bloque se centra en el espacio disponible.
    """
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    box.set_valign(Gtk.Align.CENTER)
    box.set_halign(Gtk.Align.CENTER)
    box.set_vexpand(True)
    box.set_margin_top(24)
    box.set_margin_bottom(24)

    icon = Gtk.Image.new_from_icon_name(icon_name)
    icon.set_pixel_size(32)
    icon.add_css_class("dim-label")
    box.append(icon)

    label = Gtk.Label(label=title)
    label.add_css_class("heading")
    box.append(label)

    if subtitle:
        sub = Gtk.Label(label=subtitle)
        sub.add_css_class("caption")
        sub.add_css_class("dim-label")
        sub.set_wrap(True)
        sub.set_justify(Gtk.Justification.CENTER)
        box.append(sub)

    return box


def fill_empty(listbox: Gtk.ListBox, icon_name: str, title: str, subtitle: str = ""):
    """Pone un estado vacio centrado dentro de un Gtk.ListBox ya vaciado.

    La clase .boxed-list dibuja un recuadro claro alrededor de las filas: con
    una sola fila de "no hay nada" quedaba un bloque claro arriba y un hueco
    oscuro debajo. Mientras esta vacia se le quita el recuadro y se centra.
    """
    listbox.remove_css_class("boxed-list")
    listbox.add_css_class("empty-list")
    listbox.set_valign(Gtk.Align.CENTER)
    listbox.set_vexpand(True)

    row = Gtk.ListBoxRow(activatable=False, selectable=False)
    row.set_child(empty_state(icon_name, title, subtitle))
    listbox.append(row)


def reset_list(listbox: Gtk.ListBox):
    """Devuelve el ListBox a su aspecto normal antes de llenarlo con filas"""
    listbox.remove_css_class("empty-list")
    listbox.add_css_class("boxed-list")
    listbox.set_valign(Gtk.Align.FILL)


def _on_main_thread(callback):
    """Envuelve un callback para que corra siempre en el hilo principal.

    El hub de senales es agnostico del toolkit y hay quien emite desde un hilo
    de fondo (TaskManager.sync_external_calendars). GTK4 no es thread-safe: si
    la vista se reconstruye desde ese hilo, GTK protesta y acaba en segfault.
    """
    def wrapper(*args, **kwargs):
        GLib.idle_add(lambda: (callback(*args, **kwargs), GLib.SOURCE_REMOVE)[1])

    return wrapper


def bind_signals(widget, pairs):
    """Suscribe un widget al hub global, en el hilo principal, y lo desuscribe
    cuando el widget se destruye.

    `signals` es un singleton de proceso: un widget que se conecta y nunca se
    desconecta sigue recibiendo eventos despues de que GTK lo haya liberado.
    Todo lo que se conecte al hub desde la UI debe pasar por aqui.

    pairs: iterable de (senal, callback)
    """
    bindings = [(signal, _on_main_thread(callback)) for signal, callback in pairs]
    for signal, wrapped in bindings:
        signal.connect(wrapped)

    def unbind(*_):
        for signal, wrapped in bindings:
            signal.disconnect(wrapped)

    widget.connect("destroy", unbind)
