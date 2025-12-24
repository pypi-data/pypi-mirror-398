class ObjectStyle:
    def __init__(self):
        self.cursor = None
        self.color = None
        self.background_color = None
        self.font_family = None
        self.font = None
        self.text_align = None
        self.flex = None
        self.display = None
        self.border = None
        self.border_bottom = None
        self.margin = None
        self.padding = None
        self.justify_content = None
        self.flex_grow = None
        self.gap = None
        self.grid_template_columns = None
        self.transition = None
        self.position = None
        self.width = None
        self.height = None
        self.background_image = None
        self.background_size = None
        self.background_repeat = None
        self.background_position = None
        self.font = None
        self.font_size = None
        self.font_weight = None
        self.text_decoration = None
        self.float = None
        self.border_radius = None
        self.box_shadow = None
        self.opacity = None
        self.trasform = None
        self.top = None
        self.left = None
        self.font_style = None
        self.font_variant = None
        self.outline = None
        self.z_index = None
        self.overflow = None
        self.overflow_x = None
        self.overflow_y = None
        self.border_top = None
        self.border_left = None
        self.border_right = None
        self.border_style = None
        self.border_color = None
        self.border_width = None
        self.background_clip = None
        self.background_origin = None
        self.backdrop_filter = None
        self.filter = None
        self.mix_blend_mode = None
        self.isolation = None
        self.object_fit = None
        self.object_position = None
        self.aspect_ratio = None
        self.min_width = None
        self.min_height = None
        self.max_width = None
        self.max_height = None
        self.place_items = None
        self.place_content = None
        self.align_items = None
        self.align_content = None
        self.align_self = None
        self.justify_items = None
        self.justify_self = None
        self.grid_template_rows = None
        self.grid_template_areas = None
        self.grid_area = None
        self.grid_row = None
        self.grid_column = None
        self.white_space = None
        self.word_wrap = None
        self.word_break = None
        self.letter_spacing = None
        self.line_height = None
        self.text_transform = None
        self.text_overflow = None
        self.user_select = None
        self.pointer_events = None
        self.backface_visibility = None
        self.perspective = None
        self.perspective_origin = None
        self.animation = None
        self.animation_duration = None
        self.animation_delay = None
        self.animation_timing_function = None
        self.animation_iteration_count = None
        self.animation_direction = None
        self.animation_fill_mode = None
        self.animation_play_state = None
        self.cursor_events = None
        self.list_style = None
        self.list_style_type = None
        self.list_style_position = None
        self.list_style_image = None
        self.clip_path = None
        self.mask = None
        self.mask_image = None
        self.mask_repeat = None
        self.mask_position = None
        self.mask_size = None
        self.columns = None
        self.column_gap = None
        self.column_rule = None
        self.column_rule_color = None
        self.column_rule_style = None
        self.column_rule_width = None
        self.column_span = None
        self.column_width = None
        self.break_after = None
        self.break_before = None
        self.break_inside = None
        self.will_change = None
        self.scroll_behavior = None
        self.scroll_margin = None
        self.scroll_margin_top = None
        self.scroll_margin_bottom = None
        self.scroll_margin_left = None
        self.scroll_margin_right = None
        self.scroll_padding = None
        self.scroll_padding_top = None
        self.scroll_padding_bottom = None
        self.scroll_padding_left = None
        self.scroll_padding_right = None
        self.scroll_snap_align = None
        self.scroll_snap_stop = None
        self.scroll_snap_type = None
        self.accent_color = None
        self.appearance = None
        self.caption_side = None
        self.empty_cells = None
        self.table_layout = None
        self.resize = None
        self.tab_size = None
        self.text_indent = None
        self.text_shadow = None
        self.text_rendering = None
        self.vertical_align = None
        self.visibility = None
        self.quotes = None
        self.counter_increment = None
        self.counter_reset = None
        self.image_rendering = None
        self.page_break_after = None
        self.page_break_before = None
        self.page_break_inside = None
        self.touch_action = None
        self.forced_color_adjust = None
        self.color_scheme = None
        self.nav_up = None
        self.nav_down = None
        self.nav_left = None
        self.nav_right = None
        self.ruby_align = None
        self.ruby_position = None
        self.ruby_span = None
        self.text_combine_upright = None
        self.text_orientation = None
        self.writing_mode = None
        self.direction = None
        self.unicode_bidi = None
        self.hyphenate_character = None
        self.hyphens = None
        self.line_break = None
        self.overflow_wrap = None
        self.shape_image_threshold = None
        self.shape_margin = None
        self.shape_outside = None
        self.offset = None
        self.offset_anchor = None
        self.offset_distance = None
        self.offset_path = None
        self.offset_position = None
        self.scrollbar_color = None
        self.scrollbar_width = None
        self.scrollbar_gutter = None
        self.text_underline_offset = None
        self.text_underline_position = None
        self.text_decoration_skip_ink = None
        self.font_optical_sizing = None
        self.font_synthesis = None
        self.font_variant_caps = None
        self.font_variant_numeric = None
        self.font_variant_position = None
        self.font_kerning = None
        self.font_feature_settings = None
        self.font_variant_ligatures = None
        self.font_variant_alternates = None
        self.font_variant_east_asian = None
        self.image_orientation = None
        self.paint_order = None
        self.vector_effect = None
        self.stroke = None
        self.stroke_width = None
        self.stroke_dasharray = None
        self.stroke_dashoffset = None
        self.stroke_linecap = None
        self.stroke_linejoin = None
        self.fill = None
        self.fill_rule = None
        self.offset_rotate = None
        self.scroll_timeline = None
        self.view_timeline = None
        self.container_type = None
        self.container_name = None
        self.animation_name = None
        self.transform = None

                

    def __iter__(self):
        return iter(self.__dict__.items())

class style:
    def __init__(self, content='{}'):
        if content in ['{}', 'block']:
            self.content = '{}'
        else:
            self.content = 'line'

        self.obj_sty = ObjectStyle()

    def __str__(self):
        return self.set()

    def set(self):
        if self.content == '{}':
            format_sty = '{\n'
            for name, var in self.obj_sty:
                if var is not None:
                    format_sty += f'  {name.replace('_', '-')}: {var};\n'
            format_sty += '}'
            if format_sty == '{\n}' : None
            return format_sty
        else:
            format_sty = '"'
            for name, var in self.obj_sty:
                if var is not None:
                    format_sty += f'{name.replace('_', '-')}:{var}; '
            format_sty += '"'
            return format_sty

class CreateStyleLine():
    def __init__(self):
        self.s = style('line')
        self.style = self.s.obj_sty
        
    def set(self) : return self.s.set()
    