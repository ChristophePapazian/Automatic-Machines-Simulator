import time
import collections
import colorsys

import arcade


TITLE = "Automatic Machines Simulator"

NO_MODIFIER = 0


def widest_text_sprite():
    """ This is stupid, there are very few ways to get the width of
    the text created by arcade and they are all ugly.
    So we just browse all the text sprite and retrieve the widest one.
    """
    return max(
        max(text_sprite.width for text_sprite in text.text_sprite_list)
        for text in arcade.text.draw_text.cache.values()
    )


def iter_other_tapes(sim, passive_cell_callback, active_cell_callback):
    for p, l, h, r, t in zip(
        sim.tape.pos,
        sim.tape.stacks[0],
        sim.tape.head,
        sim.tape.stacks[1],
        range(sim.am.nb_tapes),
    ):
        k = p - 1
        for c in reversed(l):
            passive_cell_callback(k, t, c)
            k -= 1
        active_cell_callback(p, t, h)
        k = p + 1
        for c in reversed(r):
            passive_cell_callback(k, t, c)
            k += 1


def is_in_bounds(x, y, s, width, height):
    """ Check if the cell centered on (x, y) and with a size s
    is in the screen boundaries.
    """
    return -s <= x <= width + s and -s <= y <= height + s


def invert_color(color):
    """ Invert the brightness of the given rgb color.
    """
    h, l, s = colorsys.rgb_to_hls(*color)
    r, g, b = map(int, colorsys.hls_to_rgb(h, 255 - l, s))
    return r, g, b


class Palette:
    def __init__(
        self,
        background_color,
        foreground_color,
        text_color,
        active_cell_background_color,
        active_cell_text_color,
        passive_cell_background_color,
        passive_cell_text_color,
    ):
        self.background_color = background_color
        self.foreground_color = foreground_color
        self.text_color = text_color
        self.active_cell_background_color = active_cell_background_color
        self.active_cell_text_color = active_cell_text_color
        self.passive_cell_background_color = passive_cell_background_color
        self.passive_cell_text_color = passive_cell_text_color

    def invert(self):
        self.background_color = invert_color(self.background_color)
        self.foreground_color = invert_color(self.foreground_color)
        self.text_color = invert_color(self.text_color)
        self.active_cell_background_color = invert_color(
            self.active_cell_background_color
        )
        self.active_cell_text_color = invert_color(self.active_cell_text_color)
        self.passive_cell_background_color = invert_color(
            self.passive_cell_background_color
        )
        self.passive_cell_text_color = invert_color(
            self.passive_cell_text_color
        )

    def __hash__(self):
        return hash(
            (
                self.background_color,
                self.foreground_color,
                self.text_color,
                self.active_cell_background_color,
                self.active_cell_text_color,
                self.passive_cell_background_color,
                self.passive_cell_text_color,
            )
        )

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, Palette):
            return False

        return (
            self.background_color == other.background_color
            and self.foreground_color == other.foreground_color
            and self.text_color == other.text_color
            and self.active_cell_background_color
            == other.active_cell_background_color
            and self.active_cell_text_color == other.active_cell_text_color
            and self.passive_cell_background_color
            == other.passive_cell_background_color
            and self.passive_cell_text_color == other.passive_cell_text_color
        )

    @classmethod
    def dark_theme(cls):
        return cls(
            background_color=(30, 30, 30),
            foreground_color=(250, 250, 250),
            text_color=(240, 240, 240),
            active_cell_background_color=(220, 215, 255),
            active_cell_text_color=(0, 0, 0),
            passive_cell_background_color=(115, 110, 155),
            passive_cell_text_color=(255, 255, 255),
        )

    @classmethod
    def light_theme(cls):
        return cls(
            background_color=(235, 235, 235),
            foreground_color=(20, 20, 20),
            text_color=(20, 20, 20),
            active_cell_background_color=(80, 65, 105),
            active_cell_text_color=(255, 255, 255),
            passive_cell_background_color=(115, 110, 155),
            passive_cell_text_color=(20, 20, 20),
        )


class Settings:
    def __init__(
        self,
        width,
        height,
        instructions_font_size,
        instructions_interspace,
        informations_font_size,
        informations_interspace,
        cell_size,
        cell_interspace,
        cell_font_size,
        passive_cell_outline_width,
        tape_wrapping_interspace,
    ):
        self.scale = 1
        self.width = width
        self.height = height
        self.center = width // 2, height // 2
        self.instructions_font_size = instructions_font_size
        self.instructions_interspace = instructions_interspace
        self.informations_interspace = informations_interspace
        self.informations_font_size = informations_font_size
        self._cell_size = cell_size
        self._cell_interspace = cell_interspace
        self._cell_font_size = cell_font_size
        self._passive_cell_outline_width = passive_cell_outline_width
        self._tape_wrapping_interspace = tape_wrapping_interspace

    @property
    def cell_size(self):
        return int(self._cell_size * self.scale)

    @property
    def cell_interspace(self):
        return int(self._cell_interspace * self.scale)

    @property
    def cell_font_size(self):
        return int(self._cell_font_size * self.scale)

    @property
    def passive_cell_outline_width(self):
        return int(self._passive_cell_outline_width * self.scale)

    @property
    def tape_wrapping_interspace(self):
        return int(self._tape_wrapping_interspace * self.scale)

    def rescale(self, coef):
        self.scale *= coef

    def zoom(self, coef, x, y):
        """ When we zoom, we want that the point at (x, y) remains stil
        while the whole screen gets scaled by the given coefficient.
        """
        cx, cy = self.center
        old_unit = self.cell_size + self.cell_interspace
        self.rescale(coef)
        new_unit = self.cell_size + self.cell_interspace
        f = new_unit / old_unit
        self.center = x - (x - cx) * f, y - (y - cy) * f

    def enlarge(self, x, y, coef=1.1):
        coef = min(10, self.scale * coef) / self.scale
        self.zoom(coef, x, y)

    def reduce(self, x, y, coef=0.9):
        """ The reduce is borned by the font size since it can't be less than 2.
        """
        coef = max(6 / self._cell_font_size, self.scale * coef) / self.scale
        self.zoom(coef, x, y)

    def move(self, dx, dy):
        self.center = self.center[0] + dx, self.center[1] + dy

    def resize(self, width, height):
        x, y = self.center
        self.center = (
            x + (width - self.width) // 2,
            y + (height - self.height) // 2,
        )
        self.width = width
        self.height = height

    @classmethod
    def default_configuration(cls):
        return cls(
            width=1024,
            height=728,
            instructions_font_size=12,
            instructions_interspace=20,
            informations_font_size=14,
            informations_interspace=20,
            cell_size=30,
            cell_interspace=2,
            cell_font_size=18,
            passive_cell_outline_width=3,
            tape_wrapping_interspace=60,
        )


class Binding:
    def __init__(self, key, arcade_bind, command):
        self.key = key
        self.arcade_bind = arcade_bind
        self.command = command

    @property
    def description(self):
        return self.command.description


class InputHandler:
    def __init__(self):
        self.key_pressed = set()
        self.bindings = []
        self.fall_back_command = None

    def number_of_bindings(self):
        return len(self.bindings)

    def register(self, binding):
        self.bindings.append(binding)
        return self

    def register_fall_back_command(self, command):
        self.fall_back_command = command
        return self

    def handle_key_press(self, key, modifier):
        self.key_pressed.add((key, modifier))

    def handle_key_release(self, key, modifier):
        self.key_pressed.discard((key, modifier))
        for binding in self.bindings:
            k, m = binding.arcade_bind
            if key == k and (m is NO_MODIFIER or modifier & m):
                return binding.command
        if key < 65505:  # Keys above are modifiers
            return self.fall_back_command

    @classmethod
    def default_bindings(cls):
        key_plus = arcade.key.EQUAL, NO_MODIFIER
        key_minus = arcade.key.KEY_6, NO_MODIFIER
        return (
            cls()
            .register(Binding("+", key_plus, SpeedUp()))
            .register(Binding("-", key_minus, SlowDown()))
            .register(Binding("p", (arcade.key.P, NO_MODIFIER), Pause()))
            .register(Binding("b", (arcade.key.B, NO_MODIFIER), Backward()))
            .register(Binding("e", (arcade.key.E, NO_MODIFIER), End()))
            .register(Binding("q", (arcade.key.Q, NO_MODIFIER), Quit()))
            .register(Binding("r", (arcade.key.R, NO_MODIFIER), Restart()))
            .register(Binding("t", (arcade.key.T, NO_MODIFIER), SwitchTheme()))
            .register_fall_back_command(NextStep())
        )


class Command:
    def __init__(self, description):
        self.description = description

    def execute(self, ui_arcade):
        pass


class NextStep(Command):
    def __init__(self):
        super().__init__("Next command")

    def execute(self, ui_arcade):
        if ui_arcade.sim.result is not None:
            arcade.close_window()
        else:
            ui_arcade.clock.pause()
            ui_arcade.sim.step()
            ui_arcade.tape_drawer.next_step()


class SpeedUp(Command):
    def __init__(self):
        super().__init__("Speed up the execution")

    def execute(self, ui_arcade):
        ui_arcade.clock.speed_up()


class SlowDown(Command):
    def __init__(self):
        super().__init__("Slow down the execution")

    def execute(self, ui_arcade):
        ui_arcade.clock.slow_down()


class Pause(Command):
    def __init__(self):
        super().__init__("Return to pause mode")

    def execute(self, ui_arcade):
        ui_arcade.clock.pause()


class Backward(Command):
    def __init__(self):
        super().__init__("Pause mode and go one step backward")

    def execute(self, ui_arcade):
        ui_arcade.clock.pause()
        ui_arcade.sim.back_step()
        ui_arcade.sim.result = None
        ui_arcade.tape_drawer.backstep()


class End(Command):
    def __init__(self):
        super().__init__(
            "Maximum speed to quickly go to the end of the computation"
        )

    def execute(self, ui_arcade):
        ui_arcade.clock.max_speed()


class Quit(Command):
    def __init__(self):
        super().__init__("Quit")

    def execute(self, ui_arcade):
        arcade.close_window()


class Restart(Command):
    def __init__(self):
        super().__init__("Restart")

    def execute(self, ui_arcade):
        ui_arcade.clock.pause()
        ui_arcade.sim.reset()
        ui_arcade.setup()


class SwitchTheme(Command):
    def __init__(self):
        super().__init__("Switch theme")

    def execute(self, ui_arcade):
        ui_arcade.palette.invert()
        ui_arcade.setup()


class FPSCounter:
    def __init__(self):
        self.time = time.perf_counter()
        self.frame_times = collections.deque(maxlen=60)

    def tick(self):
        t1 = time.perf_counter()
        dt = t1 - self.time
        self.time = t1
        self.frame_times.append(dt)

    def get_fps(self):
        total_time = sum(self.frame_times)
        if total_time == 0:
            return 0
        else:
            return len(self.frame_times) / sum(self.frame_times)


class Clock:
    def __init__(self):
        self._delay = 0
        self.time_elapsed = 0
        self.listeners = []

    def add_on_tick_listener(self, listener):
        self.listeners.append(listener)

    def get_delay(self):
        return self._delay

    def set_delay(self, delay):
        self.time_elapsed = 0
        self._delay = delay

    delay = property(get_delay, set_delay)

    def update(self, delta_time):
        self.time_elapsed += delta_time
        if self.time_elapsed >= self.delay > 0:
            self.time_elapsed -= self.delay
            for listener in self.listeners:
                listener.notify()

    def pause(self):
        self.delay = 0

    def speed_up(self):
        self.delay = 0.25 if self.delay == 0 else self.delay * 0.5

    def slow_down(self):
        self.delay = 0 if self.delay >= 2 else self.delay * 2

    def max_speed(self):
        self.delay = 1e-6


class Listener:
    def notify(self):
        pass


class Runner(Listener):
    def __init__(self, clock, sim):
        self.clock = clock
        self.sim = sim

    def notify(self):
        if self.sim.result is None:
            self.sim.step()
        else:
            self.clock.pause()


class TapeDrawerUpdate(Listener):
    def __init__(self, tape_drawer):
        self.tape_drawer = tape_drawer

    def notify(self):
        self.tape_drawer.next_step()


class Cell:
    def __init__(self, parent, x, y, text, is_active, sim, palette, settings):
        self.parent = parent
        self.x = x
        self.y = y
        self.text = text
        self.is_active = is_active
        self.sim = sim
        self.palette = palette
        self.settings = settings
        self.shapes = self._shapes()
        self.parent.add_shapes(self.shapes)

    @property
    def center(self):
        return (
            self.parent.shape_element_list.center_x,
            self.parent.shape_element_list.center_y,
        )

    def create_shape(self, x, y):
        if self.is_active:
            return arcade.create_rectangle_filled(
                x,
                y,
                self.settings.cell_size,
                self.settings.cell_size,
                self.palette.active_cell_background_color,
            )
        cell_size = self.settings.cell_size
        outline = self.settings.passive_cell_outline_width
        return arcade.create_rectangle_outline(
            x,
            y,
            cell_size - outline,
            cell_size - outline,
            self.palette.passive_cell_background_color,
            outline,
        )

    def _shapes(self):
        sep = self.settings.cell_size + self.settings.cell_interspace
        width, height = self.settings.width, self.settings.height
        if not is_in_bounds(self.x, self.y, sep, width, height):
            return ()
        x, y = self.x - self.center[0], self.y - self.center[1]
        shape = self.create_shape(x, y)
        tape_wrap_space = self.settings.tape_wrapping_interspace
        tapes_height = self.sim.tape.N * sep + tape_wrap_space
        if self.x < sep:
            return shape, self.create_shape(width + x, y + tapes_height)
        elif self.x > width - sep:
            return shape, self.create_shape(x - width, y - tapes_height)
        return (shape,)

    def activate(self, text):
        self.text = text
        self.is_active = True
        self.parent.remove_shapes(self.shapes)
        self.shapes = self._shapes()
        self.parent.add_shapes(self.shapes)

    def deactivate(self):
        self.is_active = False
        self.parent.remove_shapes(self.shapes)
        self.shapes = self._shapes()
        self.parent.add_shapes(self.shapes)

    @property
    def number_of_shapes(self):
        return len(self.shapes)

    def move(self, dx, dy):
        width, height = self.settings.width, self.settings.height
        sep = self.settings.cell_size + self.settings.cell_interspace
        prev_x, prev_y = self.x, self.y
        x, y = self.x + dx, self.y + dy
        nb_of_wrap, self.x = divmod(x, width)
        offset = self.sim.tape.N * sep + self.settings.tape_wrapping_interspace
        self.y = y - offset * nb_of_wrap
        previous_is_safe = is_in_bounds(prev_x, prev_y, -sep, width, height)
        current_is_safe = is_in_bounds(self.x, self.y, -sep, width, height)
        if not is_in_bounds(self.x, self.y, sep, width, height):
            self.parent.remove_shapes(self.shapes)
            self.shapes = ()
        elif self.number_of_shapes == 0:
            self.shapes = self._shapes()
            self.parent.add_shapes(self.shapes)
        elif previous_is_safe != current_is_safe or nb_of_wrap != 0:
            self.parent.remove_shapes(self.shapes)
            self.shapes = self._shapes()
            self.parent.add_shapes(self.shapes)


class TapeDrawer:
    def __init__(self, sim, palette, settings):
        self.sim = sim
        self.palette = palette
        self.settings = settings
        self.shape_element_list = None
        self.cells = None
        self.tapes = None
        self.active_cells = None

    def setup(self):
        self.shape_element_list = arcade.ShapeElementList()
        self.cells = set()
        self.tapes = [{} for _ in range(self.sim.tape.N)]
        self.active_cells = {}
        iter_other_tapes(
            self.sim, self.create_passive_cell, self.create_active_cell
        )

    def position_tape_to_xy(self, position, tape):
        number_of_tapes = self.sim.tape.N
        sep = self.settings.cell_size + self.settings.cell_interspace
        center_x, center_y = self.settings.center
        temp_x, temp_y = center_x + position * sep, center_y - tape * sep
        nb_of_wrap, x = divmod(temp_x, self.settings.width)
        offset = number_of_tapes * sep + self.settings.tape_wrapping_interspace
        y = temp_y - offset * nb_of_wrap
        return x, y

    def create_passive_cell(self, position, tape, text):
        self._create_cell(position, tape, text, False)

    def create_active_cell(self, position, tape, text):
        self._create_cell(position, tape, text, True)

    def _create_cell(self, position, tape, text, is_active):
        x, y = self.position_tape_to_xy(position, tape)
        cell = Cell(
            self, x, y, text, is_active, self.sim, self.palette, self.settings
        )
        self.cells.add(cell)
        self.tapes[tape][position] = cell
        if is_active:
            self.active_cells[tape] = cell

    def draw(self):
        self.shape_element_list.draw()
        iter_other_tapes(
            self.sim, self.draw_passive_text, self.draw_active_text
        )

    def draw_passive_text(self, position, tape, text):
        self.draw_text(
            position, tape, text, self.palette.passive_cell_text_color
        )

    def draw_active_text(self, position, tape, text):
        self.draw_text(
            position, tape, text, self.palette.active_cell_text_color
        )

    def draw_text(self, position, tape, text, color):
        x, y = self.position_tape_to_xy(position, tape)
        width, height = self.settings.width, self.settings.height
        if is_in_bounds(x, y, self.settings.cell_size, width, height):
            arcade.draw_text(
                text,
                x,
                y,
                color,
                self.settings.cell_font_size,
                align="center",
                anchor_x="center",
                anchor_y="center",
                bold=True,
                font_name="arial",
            )

    def next_step(self):
        for t, (p, h) in enumerate(zip(self.sim.tape.pos, self.sim.tape.head)):
            self.update_cell(p, t, h)

    backstep = next_step

    def update_cell(self, position, tape, text):
        self.active_cells[tape].deactivate()
        if position in self.tapes[tape]:
            self.tapes[tape][position].activate(text)
        else:
            self.create_active_cell(position, tape, text)
        self.active_cells[tape] = self.tapes[tape][position]

    def move(self, dx, dy):
        self.shape_element_list.move(dx, dy)
        for cell in self.cells:
            cell.move(dx, dy)

    def add_shape(self, shape):
        self.shape_element_list.append(shape)

    def add_shapes(self, shapes):
        for shape in shapes:
            self.add_shape(shape)

    def remove_shape(self, shape):
        self.shape_element_list.remove(shape)
        # There is a bug with she ShapeElementList which makes
        # it crash if we remove all the items from the list.
        # So if the list is empty, we create another one and
        # everything is alright.
        if len(self.shape_element_list) == 0:
            self.shape_element_list = arcade.ShapeElementList()

    def remove_shapes(self, shapes):
        for shape in shapes:
            self.remove_shape(shape)


class UI_Arcade(arcade.Window):
    def __init__(self, sim, palette=None, settings=None, input_handler=None):
        s = settings or Settings.default_configuration()
        super().__init__(s.width, s.height, TITLE, resizable=True)
        self.sim = sim
        self.palette = palette or Palette.dark_theme()
        self.settings = s
        self.input_handler = input_handler or InputHandler.default_bindings()
        self.tape_drawer = TapeDrawer(self.sim, self.palette, self.settings)
        self.clock = Clock()
        self.clock.add_on_tick_listener(Runner(self.clock, self.sim))
        self.clock.add_on_tick_listener(TapeDrawerUpdate(self.tape_drawer))
        self.fps = FPSCounter()

    def run(self):
        self.setup()
        arcade.run()

    def setup(self):
        arcade.set_background_color(self.palette.background_color)
        self.tape_drawer.setup()

    def draw_instructions(self):
        font_size = self.settings.informations_font_size
        interspace = self.settings.instructions_interspace
        n = self.input_handler.number_of_bindings()

        arcade.draw_text(
            f"Instructions :",
            20,
            self.height - 10 - interspace,
            self.palette.text_color,
            font_size + 2,
        )
        max_key_size = max(len(b.key) for b in self.input_handler.bindings) + 2

        for i, b in enumerate(self.input_handler.bindings, 3):
            arcade.draw_text(
                f"{b.key:^{max_key_size}} {b.description}",
                50,
                self.height - interspace * i,
                self.palette.text_color,
                font_size,
            )
        arcade.draw_text(
            "You can drag and drop the tapes with the mouse left click",
            30,
            self.height - 10 - interspace * (n + 3),
            self.palette.text_color,
            font_size,
        )
        arcade.draw_text(
            "You can scroll to zoom in / out",
            30,
            self.height - 10 - interspace * (n + 4),
            self.palette.text_color,
            font_size,
        )
        width = 60 + widest_text_sprite()
        height = (n + 5) * interspace
        arcade.draw_xywh_rectangle_outline(
            1,
            self.height - height,
            width,
            height - 1,
            self.palette.foreground_color,
        )

    def draw_informations(self):
        font_size = self.settings.informations_font_size
        interspace = self.settings.informations_interspace
        delay_text = self.clock.delay if self.clock.delay else "PAUSE"
        infos = [
            f"delay : {delay_text}",
            f"steps : {self.sim.steps}",
            f"state : {self.sim.state}",
        ]
        if self.sim.result:
            infos.append(f"result : {self.sim.result}")

        height = (len(infos) + 4) * interspace
        arcade.draw_text(
            f"Informations :",
            20,
            height - 10 - interspace,
            self.palette.text_color,
            font_size + 2,
        )

        for i, info in enumerate(infos, 3):
            arcade.draw_text(
                info,
                50,
                height - interspace * i,
                self.palette.text_color,
                font_size,
            )

        width = 60 + widest_text_sprite()
        arcade.draw_xywh_rectangle_outline(
            1, 1, width, height, self.palette.foreground_color
        )

    def draw_fps(self):
        fps = self.fps.get_fps()
        arcade.draw_text(
            f"FPS: {fps:3.0f}",
            self.width - 60,
            self.height - 20,
            self.palette.text_color,
        )
        self.fps.tick()

    def on_draw(self):
        arcade.start_render()
        self.tape_drawer.draw()
        self.draw_fps()
        self.draw_instructions()
        self.draw_informations()

    def update(self, delta_time):
        self.clock.update(delta_time)

    def on_key_press(self, key, key_modifiers):
        command = self.input_handler.handle_key_press(key, key_modifiers)
        if command:
            command.execute(self)

    def on_key_release(self, key, key_modifiers):
        command = self.input_handler.handle_key_release(key, key_modifiers)
        if command:
            command.execute(self)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if buttons == arcade.MOUSE_BUTTON_LEFT:
            self.settings.move(dx, dy)
            self.tape_drawer.move(dx, dy)

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        if scroll_y > 0:
            self.settings.enlarge(x, y, 1.1 * scroll_y)
        elif scroll_y < 0:
            self.settings.reduce(x, y, 0.9 / -scroll_y)
        self.setup()

    def on_resize(self, width, height):
        super().on_resize(width, height)
        self.settings.resize(width, height)
        self.setup()
