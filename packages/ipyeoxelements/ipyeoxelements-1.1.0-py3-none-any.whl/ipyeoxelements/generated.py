import anywidget
import traitlets
from ipywidgets import DOMWidget

# AUTOMATICALLY GENERATED FILE. DO NOT EDIT MANUALLY.


class EOxChart(anywidget.AnyWidget, DOMWidget):
    """Chart component based on [Vega-Lite](https://vega.github.io/vega-lite/)/[Vega-Embed](https://github.com/vega/vega-embed).
Pass a valid Vega spec as `spec` property in order to render a chart.

The `eox-chart` provides some default `spec` settings (merged with the provided `spec` property) and helper functionalities on top of Vega-Lite.

Default `spec` settings (see the file `src/enums/default-spec.js`):
- `width`: "container" (make the chart width responsive to the parent)
- `height`: "container" (make the chart height responsive to the parent)
- `autosize`: "fit" (automatically adjust the layout in an attempt to force the total visualization size to fit within the given width, height and padding values)
- `resize`: true (autosize layout is re-calculated on every view update)
- `padding`: 16 (the padding in pixels to add around the visualization)

These default `spec` settings can be overwritten by setting them to a differnt value in the `spec` property passed to `eox-chart`. Also, there are default
Vega-Embed options (see the file `src/enums/default-opt.js`), which can also be overwritten in the passed `opt` property.

Helper functionalities:

The `eox-chart` automatically emits mouse/pointer events from the Vega-Lite chart. See below for the emitted events."""
    _esm = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    _esm_template = """
    {imports_str}

    export default {
        render(view) {
            const tag_name = 'eox-chart';
            
            function init() {
                if (view.el.querySelector(tag_name)) return;
                const el = document.createElement(tag_name);
                el.style.width = "100%";
                el.style.height = "100%";

                // Apply Properties
                
        const id = view.model.get('id');
        if (id !== null) { el.id = id; }
    

            {
                const spec = view.model.get('spec');
                if (spec !== null) {
                    el['spec'] = spec;
                }
            }

            {
                const opt = view.model.get('opt');
                if (opt !== null) {
                    el['opt'] = opt;
                }
            }

            {
                const data_values = view.model.get('data_values');
                if (data_values !== null) {
                    el['dataValues'] = data_values;
                }
            }

            {
                const no_shadow = view.model.get('no_shadow');
                if (no_shadow !== null) {
                    el['noShadow'] = no_shadow;
                }
            }

            {
                const unstyled = view.model.get('unstyled');
                if (unstyled !== null) {
                    el['unstyled'] = unstyled;
                }
            }

                // Add Listeners
                
        view.model.on('change:id', () => { el.id = view.model.get('id'); });
    

            view.model.on('change:spec', () => {
                el['spec'] = view.model.get('spec');
            });

            view.model.on('change:opt', () => {
                el['opt'] = view.model.get('opt');
            });

            view.model.on('change:data_values', () => {
                el['dataValues'] = view.model.get('data_values');
            });

            view.model.on('change:no_shadow', () => {
                el['noShadow'] = view.model.get('no_shadow');
            });

            view.model.on('change:unstyled', () => {
                el['unstyled'] = view.model.get('unstyled');
            });
                
                // Add Method Listener
                
                view.model.on("msg:custom", (content) => {
                    if (content.type === "call_method") {
                        const methodName = content.name;
                        const args = content.args;
                        if (typeof el[methodName] === 'function') {
                            el[methodName](...args);
                        }
                    }
                });
    

                view.el.appendChild(el);
            }

            init();
        }
    }
    """


    def __init__(self, version="latest", **kwargs):
        imports = []
        # Dependencies
        imports.extend([])
        
        # Dynamic imports
        pkg_name = "chart"
        
        # Extra imports
        extra_paths = []
        for path in extra_paths:
            imports.append(f"https://cdn.jsdelivr.net/npm/@eox/{pkg_name}@{version}/{path}")
            
        # Main import
        imports.append(f"https://cdn.jsdelivr.net/npm/@eox/{pkg_name}@{version}/dist/eox-chart.js")
        
        imports_str = "\n    ".join([f'import "{url}";' for url in imports])
        
        kwargs['_esm'] = self._esm_template.replace("{imports_str}", imports_str)
        
        super().__init__(**kwargs)
    

    id = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    spec = traitlets.Any(None, allow_none=True).tag(sync=True)
    opt = traitlets.Any(None, allow_none=True).tag(sync=True)
    data_values = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    no_shadow = traitlets.Any(None, allow_none=True).tag(sync=True)
    unstyled = traitlets.Any(None, allow_none=True).tag(sync=True)



class EOxDrawtools(anywidget.AnyWidget, DOMWidget):
    """The `eox-drawtools` element provides a comprehensive set of drawing, editing, selection, and import tools for vector features on an `eox-map`. It supports drawing multiple feature types (Polygon, Box, Point, Circle, LineString), continuous drawing, feature modification, selection from existing layers, and import/export in various formats (GeoJSON, WKT, native OL feature).

Key features:
- Draw polygons, boxes, points, circles, and lines on the map
- Draw multiple features at once (set `multiple-features`)
- Continuous drawing mode (set `continuous`)
- Modify drawn features (set `allow-modify`)
- Select features from a specified layer (`layer-id`)
- Display a list of drawn/selected features (`show-list`)
- Edit features as GeoJSON in a text editor (`show-editor`)
- Import features via drag-and-drop or file upload (`import-features`)
- Emit drawn features in different formats (`format`: `feature`, `geojson`, `wkt`)
- Emit features in a specified projection (`projection`)
- Customizable feature styles (`featureStyles`)
- Unstyled and no-shadow variants for easy integration

Usage examples and visual demos are available in Storybook stories, including scenarios for multi-feature drawing, feature modification, selection, import/export, continuous drawing, format and projection control, and style customization."""
    _esm = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    _esm_template = """
    {imports_str}

    export default {
        render(view) {
            const tag_name = 'eox-drawtools';
            
            function init() {
                if (view.el.querySelector(tag_name)) return;
                const el = document.createElement(tag_name);
                el.style.width = "100%";
                el.style.height = "100%";

                // Apply Properties
                
        const id = view.model.get('id');
        if (id !== null) { el.id = id; }
    

            {
                const continuous = view.model.get('continuous');
                if (continuous !== null) {
                    el['continuous'] = continuous;
                }
            }

            {
                const layer_id = view.model.get('layer_id');
                if (layer_id !== null) {
                    el['layerId'] = layer_id;
                }
            }

            {
                const eox_map = view.model.get('eox_map');
                if (eox_map !== null) {
                    el['eoxMap'] = eox_map;
                }
            }

            {
                const allow_modify = view.model.get('allow_modify');
                if (allow_modify !== null) {
                    el['allowModify'] = allow_modify;
                }
            }

            {
                const for_ = view.model.get('for_');
                if (for_ !== null) {
                    const checkExist = setInterval(() => {
                       if (document.querySelector(for_)) {
                          el['for'] = for_;
                          clearInterval(checkExist);
                       }
                    }, 100);
                    setTimeout(() => clearInterval(checkExist), 10000);
                }
            }

            {
                const currently_drawing = view.model.get('currently_drawing');
                if (currently_drawing !== null) {
                    el['currentlyDrawing'] = currently_drawing;
                }
            }

            {
                const draw = view.model.get('draw');
                if (draw !== null) {
                    el['draw'] = draw;
                }
            }

            {
                const draw_layer = view.model.get('draw_layer');
                if (draw_layer !== null) {
                    el['drawLayer'] = draw_layer;
                }
            }

            {
                const drawn_features = view.model.get('drawn_features');
                if (drawn_features !== null) {
                    el['drawnFeatures'] = drawn_features;
                }
            }

            {
                const feature_name = view.model.get('feature_name');
                if (feature_name !== null) {
                    el['featureName'] = feature_name;
                }
            }

            {
                const feature_name_key = view.model.get('feature_name_key');
                if (feature_name_key !== null) {
                    el['featureNameKey'] = feature_name_key;
                }
            }

            {
                const feature_styles = view.model.get('feature_styles');
                if (feature_styles !== null) {
                    el['featureStyles'] = feature_styles;
                }
            }

            {
                const modify = view.model.get('modify');
                if (modify !== null) {
                    el['modify'] = modify;
                }
            }

            {
                const multiple_features = view.model.get('multiple_features');
                if (multiple_features !== null) {
                    el['multipleFeatures'] = multiple_features;
                }
            }

            {
                const import_features = view.model.get('import_features');
                if (import_features !== null) {
                    el['importFeatures'] = import_features;
                }
            }

            {
                const show_editor = view.model.get('show_editor');
                if (show_editor !== null) {
                    el['showEditor'] = show_editor;
                }
            }

            {
                const show_list = view.model.get('show_list');
                if (show_list !== null) {
                    el['showList'] = show_list;
                }
            }

            {
                const projection = view.model.get('projection');
                if (projection !== null) {
                    el['projection'] = projection;
                }
            }

            {
                const type = view.model.get('type');
                if (type !== null) {
                    el['type'] = type;
                }
            }

            {
                const selection_events = view.model.get('selection_events');
                if (selection_events !== null) {
                    el['selectionEvents'] = selection_events;
                }
            }

            {
                const format = view.model.get('format');
                if (format !== null) {
                    el['format'] = format;
                }
            }

            {
                const unstyled = view.model.get('unstyled');
                if (unstyled !== null) {
                    el['unstyled'] = unstyled;
                }
            }

            {
                const no_shadow = view.model.get('no_shadow');
                if (no_shadow !== null) {
                    el['noShadow'] = no_shadow;
                }
            }

                // Add Listeners
                
        view.model.on('change:id', () => { el.id = view.model.get('id'); });
    

            view.model.on('change:continuous', () => {
                el['continuous'] = view.model.get('continuous');
            });

            view.model.on('change:layer_id', () => {
                el['layerId'] = view.model.get('layer_id');
            });

            view.model.on('change:eox_map', () => {
                el['eoxMap'] = view.model.get('eox_map');
            });

            view.model.on('change:allow_modify', () => {
                el['allowModify'] = view.model.get('allow_modify');
            });

            view.model.on('change:for_', () => {
                const val = view.model.get('for_');
                const checkExist = setInterval(() => {
                   if (document.querySelector(val)) {
                      el['for'] = val;
                      clearInterval(checkExist);
                   }
                }, 100);
                setTimeout(() => clearInterval(checkExist), 10000);
            });

            view.model.on('change:currently_drawing', () => {
                el['currentlyDrawing'] = view.model.get('currently_drawing');
            });

            view.model.on('change:draw', () => {
                el['draw'] = view.model.get('draw');
            });

            view.model.on('change:draw_layer', () => {
                el['drawLayer'] = view.model.get('draw_layer');
            });

            view.model.on('change:drawn_features', () => {
                el['drawnFeatures'] = view.model.get('drawn_features');
            });

            view.model.on('change:feature_name', () => {
                el['featureName'] = view.model.get('feature_name');
            });

            view.model.on('change:feature_name_key', () => {
                el['featureNameKey'] = view.model.get('feature_name_key');
            });

            view.model.on('change:feature_styles', () => {
                el['featureStyles'] = view.model.get('feature_styles');
            });

            view.model.on('change:modify', () => {
                el['modify'] = view.model.get('modify');
            });

            view.model.on('change:multiple_features', () => {
                el['multipleFeatures'] = view.model.get('multiple_features');
            });

            view.model.on('change:import_features', () => {
                el['importFeatures'] = view.model.get('import_features');
            });

            view.model.on('change:show_editor', () => {
                el['showEditor'] = view.model.get('show_editor');
            });

            view.model.on('change:show_list', () => {
                el['showList'] = view.model.get('show_list');
            });

            view.model.on('change:projection', () => {
                el['projection'] = view.model.get('projection');
            });

            view.model.on('change:type', () => {
                el['type'] = view.model.get('type');
            });

            view.model.on('change:selection_events', () => {
                el['selectionEvents'] = view.model.get('selection_events');
            });

            view.model.on('change:format', () => {
                el['format'] = view.model.get('format');
            });

            view.model.on('change:unstyled', () => {
                el['unstyled'] = view.model.get('unstyled');
            });

            view.model.on('change:no_shadow', () => {
                el['noShadow'] = view.model.get('no_shadow');
            });
                
                // Add Method Listener
                
                view.model.on("msg:custom", (content) => {
                    if (content.type === "call_method") {
                        const methodName = content.name;
                        const args = content.args;
                        if (typeof el[methodName] === 'function') {
                            el[methodName](...args);
                        }
                    }
                });
    

                view.el.appendChild(el);
            }

            
            const check = setInterval(() => {
                if (document.querySelector('eox-map')) {
                    clearInterval(check);
                    init();
                }
            }, 100);
            setTimeout(() => {
                if (check) clearInterval(check);
                if (!view.el.querySelector(tag_name)) init(); 
            }, 5000);
        
        }
    }
    """


    def __init__(self, version="latest", **kwargs):
        imports = []
        # Dependencies
        imports.extend([])
        
        # Dynamic imports
        pkg_name = "drawtools"
        
        # Extra imports
        extra_paths = []
        for path in extra_paths:
            imports.append(f"https://cdn.jsdelivr.net/npm/@eox/{pkg_name}@{version}/{path}")
            
        # Main import
        imports.append(f"https://cdn.jsdelivr.net/npm/@eox/{pkg_name}@{version}/dist/eox-drawtools.js")
        
        imports_str = "\n    ".join([f'import "{url}";' for url in imports])
        
        kwargs['_esm'] = self._esm_template.replace("{imports_str}", imports_str)
        
        super().__init__(**kwargs)
    

    id = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    continuous = traitlets.Bool(False).tag(sync=True)
    layer_id = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    eox_map = traitlets.Any(None, allow_none=True).tag(sync=True)
    allow_modify = traitlets.Bool(False).tag(sync=True)
    for_ = traitlets.Any(None, allow_none=True).tag(sync=True)
    currently_drawing = traitlets.Bool(False).tag(sync=True)
    draw = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    draw_layer = traitlets.Any(None, allow_none=True).tag(sync=True)
    drawn_features = traitlets.List(None, allow_none=True).tag(sync=True)
    feature_name = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    feature_name_key = traitlets.Any(None, allow_none=True).tag(sync=True)
    feature_styles = traitlets.Any(None, allow_none=True).tag(sync=True)
    modify = traitlets.Any(None, allow_none=True).tag(sync=True)
    multiple_features = traitlets.Bool(False).tag(sync=True)
    import_features = traitlets.Bool(False).tag(sync=True)
    show_editor = traitlets.Bool(False).tag(sync=True)
    show_list = traitlets.Bool(False).tag(sync=True)
    projection = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    type = traitlets.Any(None, allow_none=True).tag(sync=True)
    selection_events = traitlets.Any(None, allow_none=True).tag(sync=True)
    format = traitlets.Any(None, allow_none=True).tag(sync=True)
    unstyled = traitlets.Bool(False).tag(sync=True)
    no_shadow = traitlets.Any(None, allow_none=True).tag(sync=True)

    def start_drawing(self, ):
        """
        Calls the 'startDrawing' method on the web component.
        """
        self.send({
            "type": "call_method",
            "name": "startDrawing",
            "args": []
        })
        

    def discard_drawing(self, ):
        """
        Calls the 'discardDrawing' method on the web component.
        """
        self.send({
            "type": "call_method",
            "name": "discardDrawing",
            "args": []
        })
        

    def handle_feature_change(self, text, replace_features, animate):
        """
        Calls the 'handleFeatureChange' method on the web component.
        """
        self.send({
            "type": "call_method",
            "name": "handleFeatureChange",
            "args": [text, replace_features, animate]
        })
        

    def handle_files_change(self, evt):
        """
        Calls the 'handleFilesChange' method on the web component.
        """
        self.send({
            "type": "call_method",
            "name": "handleFilesChange",
            "args": [evt]
        })
        

    def on_modify_end(self, ):
        """
        Calls the 'onModifyEnd' method on the web component.
        """
        self.send({
            "type": "call_method",
            "name": "onModifyEnd",
            "args": []
        })
        

    def update_geo_j_s_o_n(self, ):
        """
        Calls the 'updateGeoJSON' method on the web component.
        """
        self.send({
            "type": "call_method",
            "name": "updateGeoJSON",
            "args": []
        })
        

    def emit_drawn_features(self, ):
        """
        Calls the 'emitDrawnFeatures' method on the web component.
        """
        self.send({
            "type": "call_method",
            "name": "emitDrawnFeatures",
            "args": []
        })
        


class EOxGeosearch(anywidget.AnyWidget, DOMWidget):
    """`eox-geosearch` provides a flexible geocoding and location search interface using the OpenCage API.
It can be used standalone or integrated with `eox-map` for interactive map zooming and result visualization.

Main features:
- Search for locations using OpenCage API
- Integrate with `eox-map` for zooming to results
- Customizable loader SVG
- Geographic extent limiting
- Tooltip support
- Additional OpenCage API parameters via args
- Button mode for compact UI
- Flexible alignment and direction options"""
    _esm = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    _esm_template = """
    {imports_str}

    export default {
        render(view) {
            const tag_name = 'eox-geosearch';
            
            function init() {
                if (view.el.querySelector(tag_name)) return;
                const el = document.createElement(tag_name);
                el.style.width = "100%";
                el.style.height = "100%";

                // Apply Properties
                
        const id = view.model.get('id');
        if (id !== null) { el.id = id; }
    

            {
                const eox_map = view.model.get('eox_map');
                if (eox_map !== null) {
                    el['eoxMap'] = eox_map;
                }
            }

            {
                const endpoint = view.model.get('endpoint');
                if (endpoint !== null) {
                    el['endpoint'] = endpoint;
                }
            }

            {
                const for_ = view.model.get('for_');
                if (for_ !== null) {
                    const checkExist = setInterval(() => {
                       if (document.querySelector(for_)) {
                          el['for'] = for_;
                          clearInterval(checkExist);
                       }
                    }, 100);
                    setTimeout(() => clearInterval(checkExist), 10000);
                }
            }

            {
                const query_parameter = view.model.get('query_parameter');
                if (query_parameter !== null) {
                    el['queryParameter'] = query_parameter;
                }
            }

            {
                const button = view.model.get('button');
                if (button !== null) {
                    el['button'] = button;
                }
            }

            {
                const label = view.model.get('label');
                if (label !== null) {
                    el['label'] = label;
                }
            }

            {
                const direction = view.model.get('direction');
                if (direction !== null) {
                    el['direction'] = direction;
                }
            }

            {
                const results_direction = view.model.get('results_direction');
                if (results_direction !== null) {
                    el['resultsDirection'] = results_direction;
                }
            }

            {
                const interval = view.model.get('interval');
                if (interval !== null) {
                    el['interval'] = interval;
                }
            }

            {
                const small = view.model.get('small');
                if (small !== null) {
                    el['small'] = small;
                }
            }

            {
                const unstyled = view.model.get('unstyled');
                if (unstyled !== null) {
                    el['unstyled'] = unstyled;
                }
            }

            {
                const loader_svg = view.model.get('loader_svg');
                if (loader_svg !== null) {
                    el['loaderSvg'] = loader_svg;
                }
            }

            {
                const extent = view.model.get('extent');
                if (extent !== null) {
                    el['extent'] = extent;
                }
            }

            {
                const tooltip = view.model.get('tooltip');
                if (tooltip !== null) {
                    el['tooltip'] = tooltip;
                }
            }

            {
                const tooltip_direction = view.model.get('tooltip_direction');
                if (tooltip_direction !== null) {
                    el['tooltipDirection'] = tooltip_direction;
                }
            }

            {
                const params = view.model.get('params');
                if (params !== null) {
                    el['params'] = params;
                }
            }

            {
                const fetch_debounced = view.model.get('fetch_debounced');
                if (fetch_debounced !== null) {
                    el['fetchDebounced'] = fetch_debounced;
                }
            }

                // Add Listeners
                
        view.model.on('change:id', () => { el.id = view.model.get('id'); });
    

            view.model.on('change:eox_map', () => {
                el['eoxMap'] = view.model.get('eox_map');
            });

            view.model.on('change:endpoint', () => {
                el['endpoint'] = view.model.get('endpoint');
            });

            view.model.on('change:for_', () => {
                const val = view.model.get('for_');
                const checkExist = setInterval(() => {
                   if (document.querySelector(val)) {
                      el['for'] = val;
                      clearInterval(checkExist);
                   }
                }, 100);
                setTimeout(() => clearInterval(checkExist), 10000);
            });

            view.model.on('change:query_parameter', () => {
                el['queryParameter'] = view.model.get('query_parameter');
            });

            view.model.on('change:button', () => {
                el['button'] = view.model.get('button');
            });

            view.model.on('change:label', () => {
                el['label'] = view.model.get('label');
            });

            view.model.on('change:direction', () => {
                el['direction'] = view.model.get('direction');
            });

            view.model.on('change:results_direction', () => {
                el['resultsDirection'] = view.model.get('results_direction');
            });

            view.model.on('change:interval', () => {
                el['interval'] = view.model.get('interval');
            });

            view.model.on('change:small', () => {
                el['small'] = view.model.get('small');
            });

            view.model.on('change:unstyled', () => {
                el['unstyled'] = view.model.get('unstyled');
            });

            view.model.on('change:loader_svg', () => {
                el['loaderSvg'] = view.model.get('loader_svg');
            });

            view.model.on('change:extent', () => {
                el['extent'] = view.model.get('extent');
            });

            view.model.on('change:tooltip', () => {
                el['tooltip'] = view.model.get('tooltip');
            });

            view.model.on('change:tooltip_direction', () => {
                el['tooltipDirection'] = view.model.get('tooltip_direction');
            });

            view.model.on('change:params', () => {
                el['params'] = view.model.get('params');
            });

            view.model.on('change:fetch_debounced', () => {
                el['fetchDebounced'] = view.model.get('fetch_debounced');
            });
                
                // Add Method Listener
                
                view.model.on("msg:custom", (content) => {
                    if (content.type === "call_method") {
                        const methodName = content.name;
                        const args = content.args;
                        if (typeof el[methodName] === 'function') {
                            el[methodName](...args);
                        }
                    }
                });
    

                view.el.appendChild(el);
            }

            
            const check = setInterval(() => {
                if (document.querySelector('eox-map')) {
                    clearInterval(check);
                    init();
                }
            }, 100);
            setTimeout(() => {
                if (check) clearInterval(check);
                if (!view.el.querySelector(tag_name)) init(); 
            }, 5000);
        
        }
    }
    """


    def __init__(self, version="latest", **kwargs):
        imports = []
        # Dependencies
        imports.extend([])
        
        # Dynamic imports
        pkg_name = "geosearch"
        
        # Extra imports
        extra_paths = []
        for path in extra_paths:
            imports.append(f"https://cdn.jsdelivr.net/npm/@eox/{pkg_name}@{version}/{path}")
            
        # Main import
        imports.append(f"https://cdn.jsdelivr.net/npm/@eox/{pkg_name}@{version}/dist/eox-geosearch.js")
        
        imports_str = "\n    ".join([f'import "{url}";' for url in imports])
        
        kwargs['_esm'] = self._esm_template.replace("{imports_str}", imports_str)
        
        super().__init__(**kwargs)
    

    id = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    eox_map = traitlets.Any(None, allow_none=True).tag(sync=True)
    endpoint = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    for_ = traitlets.Any(None, allow_none=True).tag(sync=True)
    query_parameter = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    button = traitlets.Bool(False).tag(sync=True)
    label = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    direction = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    results_direction = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    interval = traitlets.Float(None, allow_none=True).tag(sync=True)
    small = traitlets.Bool(False).tag(sync=True)
    unstyled = traitlets.Bool(False).tag(sync=True)
    loader_svg = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    extent = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    tooltip = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    tooltip_direction = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    params = traitlets.Dict(None, allow_none=True).tag(sync=True)
    fetch_debounced = traitlets.Any(None, allow_none=True).tag(sync=True)

    def on_input(self, e):
        """
        Calls the 'onInput' method on the web component.
        """
        self.send({
            "type": "call_method",
            "name": "onInput",
            "args": [e]
        })
        

    def on_input_blur(self, ):
        """
        Calls the 'onInputBlur' method on the web component.
        """
        self.send({
            "type": "call_method",
            "name": "onInputBlur",
            "args": []
        })
        

    def handle_select(self, event):
        """
        Calls the 'handleSelect' method on the web component.
        """
        self.send({
            "type": "call_method",
            "name": "handleSelect",
            "args": [event]
        })
        

    def update_map(self, ):
        """
        Calls the 'updateMap' method on the web component.
        """
        self.send({
            "type": "call_method",
            "name": "updateMap",
            "args": []
        })
        


class EOxJsonform(anywidget.AnyWidget, DOMWidget):
    """`eox-jsonform` is a flexible and extensible web component for rendering dynamic forms based on JSON schema definitions.
It is based on [JSON Editor](https://github.com/json-editor/json-editor) and extends its functionality to support various advanced features.
Also check out the [JSON Editor documentation](https://github.com/json-editor/json-editor?tab=readme-ov-file#options) for more details on the available options and configurations.

Features:
- Renders forms from JSON schema, supporting complex nested structures and custom validation.
- All properties and event handlers are passed via args, enabling dynamic configuration and integration.
- Supports custom editor interfaces for advanced input types and external editor integration (e.g., Ace, Markdown, spatial drawtools).
- Handles spatial inputs (bounding box, polygons, points, lines) and outputs in various formats (GeoJSON, WKT).
- Allows toggling and opt-in/optional properties, with dynamic visibility and value updates.
- Can load schema and values from external URLs, supporting async loading and ready events.
- Integrates with `eox-map` for spatial feature selection when required.
- Supports unstyled rendering for custom design integration.

See the stories for usage examples covering validation, custom editors, spatial inputs, opt-in/optional properties, external loading, and more."""
    _esm = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    _esm_template = """
    {imports_str}

    export default {
        render(view) {
            const tag_name = 'eox-jsonform';
            
            function init() {
                if (view.el.querySelector(tag_name)) return;
                const el = document.createElement(tag_name);
                el.style.width = "100%";
                el.style.height = "100%";

                // Apply Properties
                
        const id = view.model.get('id');
        if (id !== null) { el.id = id; }
    

            {
                const editor = view.model.get('editor');
                if (editor !== null) {
                    el['editor'] = editor;
                }
            }

            {
                const schema = view.model.get('schema');
                if (schema !== null) {
                    el['schema'] = schema;
                }
            }

            {
                const value = view.model.get('value');
                if (value !== null) {
                    el['value'] = value;
                }
            }

            {
                const options = view.model.get('options');
                if (options !== null) {
                    el['options'] = options;
                }
            }

            {
                const no_shadow = view.model.get('no_shadow');
                if (no_shadow !== null) {
                    el['noShadow'] = no_shadow;
                }
            }

            {
                const properties_toggle = view.model.get('properties_toggle');
                if (properties_toggle !== null) {
                    el['propertiesToggle'] = properties_toggle;
                }
            }

            {
                const unstyled = view.model.get('unstyled');
                if (unstyled !== null) {
                    el['unstyled'] = unstyled;
                }
            }

            {
                const custom_editor_interfaces = view.model.get('custom_editor_interfaces');
                if (custom_editor_interfaces !== null) {
                    el['customEditorInterfaces'] = custom_editor_interfaces;
                }
            }

                // Add Listeners
                
        view.model.on('change:id', () => { el.id = view.model.get('id'); });
    

            view.model.on('change:editor', () => {
                el['editor'] = view.model.get('editor');
            });

            view.model.on('change:schema', () => {
                el['schema'] = view.model.get('schema');
            });

            view.model.on('change:value', () => {
                el['value'] = view.model.get('value');
            });

            view.model.on('change:options', () => {
                el['options'] = view.model.get('options');
            });

            view.model.on('change:no_shadow', () => {
                el['noShadow'] = view.model.get('no_shadow');
            });

            view.model.on('change:properties_toggle', () => {
                el['propertiesToggle'] = view.model.get('properties_toggle');
            });

            view.model.on('change:unstyled', () => {
                el['unstyled'] = view.model.get('unstyled');
            });

            view.model.on('change:custom_editor_interfaces', () => {
                el['customEditorInterfaces'] = view.model.get('custom_editor_interfaces');
            });
                
                // Add Method Listener
                
                view.model.on("msg:custom", (content) => {
                    if (content.type === "call_method") {
                        const methodName = content.name;
                        const args = content.args;
                        if (typeof el[methodName] === 'function') {
                            el[methodName](...args);
                        }
                    }
                });
    

                view.el.appendChild(el);
            }

            init();
        }
    }
    """


    def __init__(self, version="latest", **kwargs):
        imports = []
        # Dependencies
        imports.extend([])
        
        # Dynamic imports
        pkg_name = "jsonform"
        
        # Extra imports
        extra_paths = []
        for path in extra_paths:
            imports.append(f"https://cdn.jsdelivr.net/npm/@eox/{pkg_name}@{version}/{path}")
            
        # Main import
        imports.append(f"https://cdn.jsdelivr.net/npm/@eox/{pkg_name}@{version}/dist/eox-jsonform.js")
        
        imports_str = "\n    ".join([f'import "{url}";' for url in imports])
        
        kwargs['_esm'] = self._esm_template.replace("{imports_str}", imports_str)
        
        super().__init__(**kwargs)
    

    id = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    editor = traitlets.Any(None, allow_none=True).tag(sync=True)
    schema = traitlets.Any(None, allow_none=True).tag(sync=True)
    value = traitlets.Any(None, allow_none=True).tag(sync=True)
    options = traitlets.Dict(None, allow_none=True).tag(sync=True)
    no_shadow = traitlets.Any(None, allow_none=True).tag(sync=True)
    properties_toggle = traitlets.Any(None, allow_none=True).tag(sync=True)
    unstyled = traitlets.Any(None, allow_none=True).tag(sync=True)
    custom_editor_interfaces = traitlets.List(None, allow_none=True).tag(sync=True)



class EOxLayercontrol(anywidget.AnyWidget, DOMWidget):
    """The `eox-layercontrol` element provides a user interface for managing and configuring layers of an `eox-map`. It connects to the underlying OpenLayers map instance and displays a list of layers, supporting advanced features such as optional layers, exclusive layers, layer tools, dynamic legends, time controls, and external layer addition.

## Usage
Place `<eox-layercontrol></eox-layercontrol>` next to an `<eox-map></eox-map>` element. If there is only one `eox-map` present, `eox-layercontrol` will automatically connect to it. This can be configured
via the `for` attribute/property in order to support connecting to a specific map.

## Layer Properties
To be displayed and managed correctly, the map layers should have custom properties set (e.g. using `properties.<property>` inside the `eox-map` layer json, or by doing `layer.set(property, value)` on the native OpenLayers layers).

- `id?: string` — Unique identifier for the layer. Recommended for referencing and managing layers; also used for `eox-map` smart layer updating.
- `title?: string` — Human-readable title for the layer, displayed in the control. Recommended for usability.
- `layerControlHide?: boolean` — If true, hides the layer from the control UI.
- `layerControlOptional?: boolean` — If true, the layer is initially hidden and can be added from the optional list.
- `layerControlExclusive?: boolean` — If true, only one exclusive layer can be visualized at a time (taking into account all other layers on the same level with this property).
- `layerControlExpand?: boolean` — If true, the layer is "expanded" by default, showing description, tools etc. (if available).
- `layerControlToolsExpand?: boolean` — If true, the layer tools section is expanded by default.
- `layerConfig?: object` — Configuration for the "config" tool, consisting of a JSON schema (rendered by `eox-jsonform`) for editable settings.
- `layerDatetime?: object` — Configuration for the "datetime" tool, supporting time-based controls and playback.
- `layerLegend?: object` — Configuration for the "legend" tool, supporting dynamic color legends.

For `eox-map` attributes/properties and emitted events, see below."""
    _esm = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    _esm_template = """
    {imports_str}

    export default {
        render(view) {
            const tag_name = 'eox-layercontrol';
            
            function init() {
                if (view.el.querySelector(tag_name)) return;
                const el = document.createElement(tag_name);
                el.style.width = "100%";
                el.style.height = "100%";

                // Apply Properties
                
        const id = view.model.get('id');
        if (id !== null) { el.id = id; }
    

            {
                const eox_map = view.model.get('eox_map');
                if (eox_map !== null) {
                    el['eoxMap'] = eox_map;
                }
            }

            {
                const for_ = view.model.get('for_');
                if (for_ !== null) {
                    const checkExist = setInterval(() => {
                       if (document.querySelector(for_)) {
                          el['for'] = for_;
                          clearInterval(checkExist);
                       }
                    }, 100);
                    setTimeout(() => clearInterval(checkExist), 10000);
                }
            }

            {
                const id_property = view.model.get('id_property');
                if (id_property !== null) {
                    el['idProperty'] = id_property;
                }
            }

            {
                const map = view.model.get('map');
                if (map !== null) {
                    el['map'] = map;
                }
            }

            {
                const title_property = view.model.get('title_property');
                if (title_property !== null) {
                    el['titleProperty'] = title_property;
                }
            }

            {
                const show_layer_zoom_state = view.model.get('show_layer_zoom_state');
                if (show_layer_zoom_state !== null) {
                    el['showLayerZoomState'] = show_layer_zoom_state;
                }
            }

            {
                const tools = view.model.get('tools');
                if (tools !== null) {
                    el['tools'] = tools;
                }
            }

            {
                const add_external_layers = view.model.get('add_external_layers');
                if (add_external_layers !== null) {
                    el['addExternalLayers'] = add_external_layers;
                }
            }

            {
                const unstyled = view.model.get('unstyled');
                if (unstyled !== null) {
                    el['unstyled'] = unstyled;
                }
            }

            {
                const style_override = view.model.get('style_override');
                if (style_override !== null) {
                    el['styleOverride'] = style_override;
                }
            }

            {
                const tools_as_list = view.model.get('tools_as_list');
                if (tools_as_list !== null) {
                    el['toolsAsList'] = tools_as_list;
                }
            }

            {
                const globally_exclusive_layers = view.model.get('globally_exclusive_layers');
                if (globally_exclusive_layers !== null) {
                    el['globallyExclusiveLayers'] = globally_exclusive_layers;
                }
            }

            {
                const custom_editor_interfaces = view.model.get('custom_editor_interfaces');
                if (custom_editor_interfaces !== null) {
                    el['customEditorInterfaces'] = custom_editor_interfaces;
                }
            }

                // Add Listeners
                
        view.model.on('change:id', () => { el.id = view.model.get('id'); });
    

            view.model.on('change:eox_map', () => {
                el['eoxMap'] = view.model.get('eox_map');
            });

            view.model.on('change:for_', () => {
                const val = view.model.get('for_');
                const checkExist = setInterval(() => {
                   if (document.querySelector(val)) {
                      el['for'] = val;
                      clearInterval(checkExist);
                   }
                }, 100);
                setTimeout(() => clearInterval(checkExist), 10000);
            });

            view.model.on('change:id_property', () => {
                el['idProperty'] = view.model.get('id_property');
            });

            view.model.on('change:map', () => {
                el['map'] = view.model.get('map');
            });

            view.model.on('change:title_property', () => {
                el['titleProperty'] = view.model.get('title_property');
            });

            view.model.on('change:show_layer_zoom_state', () => {
                el['showLayerZoomState'] = view.model.get('show_layer_zoom_state');
            });

            view.model.on('change:tools', () => {
                el['tools'] = view.model.get('tools');
            });

            view.model.on('change:add_external_layers', () => {
                el['addExternalLayers'] = view.model.get('add_external_layers');
            });

            view.model.on('change:unstyled', () => {
                el['unstyled'] = view.model.get('unstyled');
            });

            view.model.on('change:style_override', () => {
                el['styleOverride'] = view.model.get('style_override');
            });

            view.model.on('change:tools_as_list', () => {
                el['toolsAsList'] = view.model.get('tools_as_list');
            });

            view.model.on('change:globally_exclusive_layers', () => {
                el['globallyExclusiveLayers'] = view.model.get('globally_exclusive_layers');
            });

            view.model.on('change:custom_editor_interfaces', () => {
                el['customEditorInterfaces'] = view.model.get('custom_editor_interfaces');
            });
                
                // Add Method Listener
                
                view.model.on("msg:custom", (content) => {
                    if (content.type === "call_method") {
                        const methodName = content.name;
                        const args = content.args;
                        if (typeof el[methodName] === 'function') {
                            el[methodName](...args);
                        }
                    }
                });
    

                view.el.appendChild(el);
            }

            
            const check = setInterval(() => {
                if (document.querySelector('eox-map')) {
                    clearInterval(check);
                    init();
                }
            }, 100);
            setTimeout(() => {
                if (check) clearInterval(check);
                if (!view.el.querySelector(tag_name)) init(); 
            }, 5000);
        
        }
    }
    """


    def __init__(self, version="latest", **kwargs):
        imports = []
        # Dependencies
        imports.extend(["https://cdn.jsdelivr.net/npm/@eox/jsonform@latest/dist/eox-jsonform.js"])
        
        # Dynamic imports
        pkg_name = "layercontrol"
        
        # Extra imports
        extra_paths = []
        for path in extra_paths:
            imports.append(f"https://cdn.jsdelivr.net/npm/@eox/{pkg_name}@{version}/{path}")
            
        # Main import
        imports.append(f"https://cdn.jsdelivr.net/npm/@eox/{pkg_name}@{version}/dist/eox-layercontrol.js")
        
        imports_str = "\n    ".join([f'import "{url}";' for url in imports])
        
        kwargs['_esm'] = self._esm_template.replace("{imports_str}", imports_str)
        
        super().__init__(**kwargs)
    

    id = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    eox_map = traitlets.Any(None, allow_none=True).tag(sync=True)
    for_ = traitlets.Any(None, allow_none=True).tag(sync=True)
    id_property = traitlets.Any(None, allow_none=True).tag(sync=True)
    map = traitlets.Any(None, allow_none=True).tag(sync=True)
    title_property = traitlets.Any(None, allow_none=True).tag(sync=True)
    show_layer_zoom_state = traitlets.Any(None, allow_none=True).tag(sync=True)
    tools = traitlets.List(None, allow_none=True).tag(sync=True)
    add_external_layers = traitlets.Any(None, allow_none=True).tag(sync=True)
    unstyled = traitlets.Any(None, allow_none=True).tag(sync=True)
    style_override = traitlets.Any(None, allow_none=True).tag(sync=True)
    tools_as_list = traitlets.Any(None, allow_none=True).tag(sync=True)
    globally_exclusive_layers = traitlets.Any(None, allow_none=True).tag(sync=True)
    custom_editor_interfaces = traitlets.List(None, allow_none=True).tag(sync=True)



class EOxMap(anywidget.AnyWidget, DOMWidget):
    """The `eox-map` element is a powerful wrapper around [OpenLayers](https://openlayers.org/) that provides a declarative, highly configurable map element for web applications. It supports a wide range of layer types, sources, controls, and advanced features, making it suitable for interactive mapping, data visualization, and geospatial analysis.

## Basic usage:

```
import "@eox/map"

<eox-map [...]></eox-map>
```

Some basic layers, sources and formats are included in the default bundle, for advanced usage it is
required to import the `advancedLayersAndSources` plugin.

Included in the base bundle:
- Formats: `GeoJSON`, `MVT`
- Layers: `Group`, `Image`, `Tile`, `Vector`, `VectorTile`
- Sources: `ImageWMS`, `OSM`, `Tile`, `TileWMS`, `Vector`, `VectorTile`, `WMTS`, `XYZ`

In order to use the rest of the layers and sources provided by OpenLayers, import the plugin as well:

```
import "@eox/map/src/plugins/advancedLayersAndSources"
import "@eox/map"

<eox-map [...]></eox-map>
```
Included in the advanced plugin bundle:
- Layers:
  - All OpenLayers layer types
  - [`STAC`](https://github.com/m-mohr/ol-stac)
- Sources:
  - All OpenLayers source types
  - [`WMTSCapabilities`](https://github.com/EOX-A/EOxElements/tree/main/elements/map/src/custom/sources/WMTSCapabilities.ts)
- Reprojection through [proj4](https://github.com/proj4js/proj4js)

For usage and story examples, see the Storybook stories in `/elements/map/stories`.

## Features

- **Layer Support:** Easily add and configure layers such as Tile, Vector, VectorTile, Image, Group, and advanced types like STAC, GeoTIFF, MapboxStyle, and FlatGeoBuf. Layers are passed via the `layers` property as an array of configuration objects.
- **Source Formats:** Supports GeoJSON, MVT, OSM, TileWMS, WMTS, XYZ, ImageWMS, and more. Advanced sources (e.g., WMTSCapabilities) are available via plugin import.
- **Controls:** Add built-in or custom controls (Zoom, Geolocation, LoadingIndicator, etc.) using the `controls` property. Controls can be configured and styled for various use cases.
- **Interactions:** Enable feature selection, hover, click, cluster-explode, and highlight interactions. Interactions are configured per layer and can trigger custom events.
- **Tooltips:** Built-in tooltip support via `<eox-map-tooltip></eox-map-tooltip>`, with options for property transformation, custom tooltips, and pixel/band value display for raster layers.
- **Layer Groups:** Organize layers into groups for complex compositions and hierarchical management.
- **Animations:** Animate view changes (zoom, center, extent) using the `animationOptions` property.
- **Projection & Transformation:** Change map projection, register custom projections, and transform coordinates/extents using helper methods.
- **Sync & Compare:** Synchronize multiple maps using the `sync` property, and compare maps side-by-side with `<eox-map-compare>`.
- **Config Object:** Pass a configuration object for advanced map setup and dynamic updates.
- **Scroll Prevention:** Prevent scroll/drag interactions for embedded maps using the `preventScroll` property.
- **Globe View:** Interactive 3D globe by using "globe" projection property.

## Events

- `clusterSelect`: Fired when a cluster is selected.
- `loadend`: Fired when the map has finished loading.
- `mapmounted`: Fired when the map is successfully mounted.
- `select`: Fired when a feature is selected.
- `layerschanged`: Fired when the layers have been changed.

## Methods

- `registerProjection`, `registerProjectionFromCode`: Register custom or EPSG projections.
- `getLayerById`, `getFlatLayersArray`: Retrieve layers by ID or as a flat array.
- `addOrUpdateLayer`, `removeInteraction`, `removeSelect`, `removeControl`: Manage layers and interactions programmatically.
- `parseFeature`: Parses a feature from the input data.
- `parseTextToFeature`: Parses text into a feature.

Usage: `document.querySelector("eox-map").registerProjection([...]);`

## Additional Helper Methods

- `buffer`: Applies a buffer around an extent
- `transform`, `transformExtent`: Transform coordinates and extents between projections.

Usage: `import { buffer, transform, transformExtent } from "@eox/map";`"""
    _esm = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    _esm_template = """
    {imports_str}

    export default {
        render(view) {
            const tag_name = 'eox-map';
            
            function init() {
                if (view.el.querySelector(tag_name)) return;
                const el = document.createElement(tag_name);
                el.style.width = "100%";
                el.style.height = "100%";

                // Apply Properties
                
        const id = view.model.get('id');
        if (id !== null) { el.id = id; }
    

            {
                const center = view.model.get('center');
                if (center !== null) {
                    el['center'] = center;
                }
            }

            {
                const config = view.model.get('config');
                if (config !== null) {
                    el['config'] = config;
                }
            }

            {
                const lon_lat_center = view.model.get('lon_lat_center');
                if (lon_lat_center !== null) {
                    el['lonLatCenter'] = lon_lat_center;
                }
            }

            {
                const lon_lat_extent = view.model.get('lon_lat_extent');
                if (lon_lat_extent !== null) {
                    el['lonLatExtent'] = lon_lat_extent;
                }
            }

            {
                const zoom = view.model.get('zoom');
                if (zoom !== null) {
                    el['zoom'] = zoom;
                }
            }

            {
                const zoom_extent = view.model.get('zoom_extent');
                if (zoom_extent !== null) {
                    el['zoomExtent'] = zoom_extent;
                }
            }

            {
                const controls = view.model.get('controls');
                if (controls !== null) {
                    el['controls'] = controls;
                }
            }

            {
                const layers = view.model.get('layers');
                if (layers !== null) {
                    el['layers'] = layers;
                }
            }

            {
                const prevent_scroll = view.model.get('prevent_scroll');
                if (prevent_scroll !== null) {
                    el['preventScroll'] = prevent_scroll;
                }
            }

            {
                const animation_options = view.model.get('animation_options');
                if (animation_options !== null) {
                    el['animationOptions'] = animation_options;
                }
            }

            {
                const projection = view.model.get('projection');
                if (projection !== null) {
                    el['projection'] = projection;
                }
            }

            {
                const o_lprojection = view.model.get('o_lprojection');
                if (o_lprojection !== null) {
                    el['OLprojection'] = o_lprojection;
                }
            }

            {
                const globe_enabled = view.model.get('globe_enabled');
                if (globe_enabled !== null) {
                    el['globeEnabled'] = globe_enabled;
                }
            }

            {
                const sync = view.model.get('sync');
                if (sync !== null) {
                    el['sync'] = sync;
                }
            }

            {
                const map = view.model.get('map');
                if (map !== null) {
                    el['map'] = map;
                }
            }

            {
                const interactions = view.model.get('interactions');
                if (interactions !== null) {
                    el['interactions'] = interactions;
                }
            }

            {
                const select_interactions = view.model.get('select_interactions');
                if (select_interactions !== null) {
                    el['selectInteractions'] = select_interactions;
                }
            }

            {
                const map_controls = view.model.get('map_controls');
                if (map_controls !== null) {
                    el['mapControls'] = map_controls;
                }
            }

            {
                const globe = view.model.get('globe');
                if (globe !== null) {
                    el['globe'] = globe;
                }
            }

                // Add Listeners
                
        view.model.on('change:id', () => { el.id = view.model.get('id'); });
    

            view.model.on('change:center', () => {
                el['center'] = view.model.get('center');
            });

            view.model.on('change:config', () => {
                el['config'] = view.model.get('config');
            });

            view.model.on('change:lon_lat_center', () => {
                el['lonLatCenter'] = view.model.get('lon_lat_center');
            });

            view.model.on('change:lon_lat_extent', () => {
                el['lonLatExtent'] = view.model.get('lon_lat_extent');
            });

            view.model.on('change:zoom', () => {
                el['zoom'] = view.model.get('zoom');
            });

            view.model.on('change:zoom_extent', () => {
                el['zoomExtent'] = view.model.get('zoom_extent');
            });

            view.model.on('change:controls', () => {
                el['controls'] = view.model.get('controls');
            });

            view.model.on('change:layers', () => {
                el['layers'] = view.model.get('layers');
            });

            view.model.on('change:prevent_scroll', () => {
                el['preventScroll'] = view.model.get('prevent_scroll');
            });

            view.model.on('change:animation_options', () => {
                el['animationOptions'] = view.model.get('animation_options');
            });

            view.model.on('change:projection', () => {
                el['projection'] = view.model.get('projection');
            });

            view.model.on('change:o_lprojection', () => {
                el['OLprojection'] = view.model.get('o_lprojection');
            });

            view.model.on('change:globe_enabled', () => {
                el['globeEnabled'] = view.model.get('globe_enabled');
            });

            view.model.on('change:sync', () => {
                el['sync'] = view.model.get('sync');
            });

            view.model.on('change:map', () => {
                el['map'] = view.model.get('map');
            });

            view.model.on('change:interactions', () => {
                el['interactions'] = view.model.get('interactions');
            });

            view.model.on('change:select_interactions', () => {
                el['selectInteractions'] = view.model.get('select_interactions');
            });

            view.model.on('change:map_controls', () => {
                el['mapControls'] = view.model.get('map_controls');
            });

            view.model.on('change:globe', () => {
                el['globe'] = view.model.get('globe');
            });
                
                // Add Method Listener
                
                view.model.on("msg:custom", (content) => {
                    if (content.type === "call_method") {
                        const methodName = content.name;
                        const args = content.args;
                        if (typeof el[methodName] === 'function') {
                            el[methodName](...args);
                        }
                    }
                });
    

                view.el.appendChild(el);
            }

            init();
        }
    }
    """


    def __init__(self, version="latest", **kwargs):
        imports = []
        # Dependencies
        imports.extend([])
        
        # Dynamic imports
        pkg_name = "map"
        
        # Extra imports
        extra_paths = ["dist/eox-map-advanced-layers-and-sources.js", "dist/eox-map-globe.js"]
        for path in extra_paths:
            imports.append(f"https://cdn.jsdelivr.net/npm/@eox/{pkg_name}@{version}/{path}")
            
        # Main import
        imports.append(f"https://cdn.jsdelivr.net/npm/@eox/{pkg_name}@{version}/dist/eox-map.js")
        
        imports_str = "\n    ".join([f'import "{url}";' for url in imports])
        
        kwargs['_esm'] = self._esm_template.replace("{imports_str}", imports_str)
        
        super().__init__(**kwargs)
    

    id = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    center = traitlets.List(None, allow_none=True).tag(sync=True)
    config = traitlets.Any(None, allow_none=True).tag(sync=True)
    lon_lat_center = traitlets.List(None, allow_none=True).tag(sync=True)
    lon_lat_extent = traitlets.List(None, allow_none=True).tag(sync=True)
    zoom = traitlets.Float(None, allow_none=True).tag(sync=True)
    zoom_extent = traitlets.List(None, allow_none=True).tag(sync=True)
    controls = traitlets.Any(None, allow_none=True).tag(sync=True)
    layers = traitlets.List(None, allow_none=True).tag(sync=True)
    prevent_scroll = traitlets.Bool(False).tag(sync=True)
    animation_options = traitlets.Any(None, allow_none=True).tag(sync=True)
    projection = traitlets.Any(None, allow_none=True).tag(sync=True)
    o_lprojection = traitlets.Any(None, allow_none=True).tag(sync=True)
    globe_enabled = traitlets.Bool(False).tag(sync=True)
    sync = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    map = traitlets.Any(None, allow_none=True).tag(sync=True)
    interactions = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    select_interactions = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    map_controls = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    globe = traitlets.Any(None, allow_none=True).tag(sync=True)

    def add_or_update_layer(self, json):
        """
        Calls the 'addOrUpdateLayer' method on the web component.
        """
        self.send({
            "type": "call_method",
            "name": "addOrUpdateLayer",
            "args": [json]
        })
        

    def remove_interaction(self, id):
        """
        Calls the 'removeInteraction' method on the web component.
        """
        self.send({
            "type": "call_method",
            "name": "removeInteraction",
            "args": [id]
        })
        

    def remove_select(self, id):
        """
        Calls the 'removeSelect' method on the web component.
        """
        self.send({
            "type": "call_method",
            "name": "removeSelect",
            "args": [id]
        })
        

    def remove_control(self, id):
        """
        Calls the 'removeControl' method on the web component.
        """
        self.send({
            "type": "call_method",
            "name": "removeControl",
            "args": [id]
        })
        

    def get_layer_by_id(self, layer_id):
        """
        Calls the 'getLayerById' method on the web component.
        """
        self.send({
            "type": "call_method",
            "name": "getLayerById",
            "args": [layer_id]
        })
        

    def parse_feature(self, features):
        """
        Calls the 'parseFeature' method on the web component.
        """
        self.send({
            "type": "call_method",
            "name": "parseFeature",
            "args": [features]
        })
        

    def parse_text_to_feature(self, text, vector_layer, e_ox_map, replace_features, animate):
        """
        Calls the 'parseTextToFeature' method on the web component.
        """
        self.send({
            "type": "call_method",
            "name": "parseTextToFeature",
            "args": [text, vector_layer, e_ox_map, replace_features, animate]
        })
        

    def register_projection_from_code(self, code):
        """
        Calls the 'registerProjectionFromCode' method on the web component.
        """
        self.send({
            "type": "call_method",
            "name": "registerProjectionFromCode",
            "args": [code]
        })
        

    def register_projection(self, name, projection, extent):
        """
        Calls the 'registerProjection' method on the web component.
        """
        self.send({
            "type": "call_method",
            "name": "registerProjection",
            "args": [name, projection, extent]
        })
        

    def get_flat_layers_array(self, layers):
        """
        Calls the 'getFlatLayersArray' method on the web component.
        """
        self.send({
            "type": "call_method",
            "name": "getFlatLayersArray",
            "args": [layers]
        })
        


class EOxStacinfo(anywidget.AnyWidget, DOMWidget):
    """### Introduction
Working with STAC catalogs, collections and items often times requires
to fetch a JSON file, parse its contents and display some of its fields
in some formatted way. To make these steps reusable, the `eox-stacinfo`
element offers a set of functionalities:
- **automatically fetch a STAC file** as soon as the element loads
- offer a **property whitelist** functionality to choose which properties to display
- display the properties in **configurable sections** (header, body, featured, footer)
- allow to **override** any property display for application-specific custom needs

The use case for this element is alongside a map which displays STAC files
or in a catalog browsing scenario where a quick look at the most important properties
is needed.

#### Technology
Under the hood, this element uses [stac-fields](https://github.com/stac-utils/stac-fields) for parsing and pre-formatting properties.

#### Usage
Place `<eox-stacinfo></eox-stacinfo>` in your application and set the `for` property to a valid STAC resource URL. The element will fetch the file and display its properties in configurable sections:
- `header`: Array of property keys to display at the top
- `tags`: Array of property keys to display as tags
- `body`: Array of property keys for the main content
- `featured`: Array of property keys for prominent display
- `footer`: Array of property keys for the bottom section

#### Customization
- **Slots**: You can override the default rendering of any property by providing a slot with the property name. This enables advanced customization and integration with application-specific UI.
- **Unstyled mode**: By setting the `unstyled` property, only minimal styles are applied, allowing for full custom styling and integration into different design systems."""
    _esm = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    _esm_template = """
    {imports_str}

    export default {
        render(view) {
            const tag_name = 'eox-stacinfo';
            
            function init() {
                if (view.el.querySelector(tag_name)) return;
                const el = document.createElement(tag_name);
                el.style.width = "100%";
                el.style.height = "100%";

                // Apply Properties
                
        const id = view.model.get('id');
        if (id !== null) { el.id = id; }
    

            {
                const allow_html = view.model.get('allow_html');
                if (allow_html !== null) {
                    el['allowHtml'] = allow_html;
                }
            }

            {
                const unstyled = view.model.get('unstyled');
                if (unstyled !== null) {
                    el['unstyled'] = unstyled;
                }
            }

            {
                const for_ = view.model.get('for_');
                if (for_ !== null) {
                    const checkExist = setInterval(() => {
                       if (document.querySelector(for_)) {
                          el['for'] = for_;
                          clearInterval(checkExist);
                       }
                    }, 100);
                    setTimeout(() => clearInterval(checkExist), 10000);
                }
            }

            {
                const header = view.model.get('header');
                if (header !== null) {
                    el['header'] = header;
                }
            }

            {
                const tags = view.model.get('tags');
                if (tags !== null) {
                    el['tags'] = tags;
                }
            }

            {
                const body = view.model.get('body');
                if (body !== null) {
                    el['body'] = body;
                }
            }

            {
                const featured = view.model.get('featured');
                if (featured !== null) {
                    el['featured'] = featured;
                }
            }

            {
                const footer = view.model.get('footer');
                if (footer !== null) {
                    el['footer'] = footer;
                }
            }

            {
                const stac_info = view.model.get('stac_info');
                if (stac_info !== null) {
                    el['stacInfo'] = stac_info;
                }
            }

            {
                const stac_properties = view.model.get('stac_properties');
                if (stac_properties !== null) {
                    el['stacProperties'] = stac_properties;
                }
            }

                // Add Listeners
                
        view.model.on('change:id', () => { el.id = view.model.get('id'); });
    

            view.model.on('change:allow_html', () => {
                el['allowHtml'] = view.model.get('allow_html');
            });

            view.model.on('change:unstyled', () => {
                el['unstyled'] = view.model.get('unstyled');
            });

            view.model.on('change:for_', () => {
                const val = view.model.get('for_');
                const checkExist = setInterval(() => {
                   if (document.querySelector(val)) {
                      el['for'] = val;
                      clearInterval(checkExist);
                   }
                }, 100);
                setTimeout(() => clearInterval(checkExist), 10000);
            });

            view.model.on('change:header', () => {
                el['header'] = view.model.get('header');
            });

            view.model.on('change:tags', () => {
                el['tags'] = view.model.get('tags');
            });

            view.model.on('change:body', () => {
                el['body'] = view.model.get('body');
            });

            view.model.on('change:featured', () => {
                el['featured'] = view.model.get('featured');
            });

            view.model.on('change:footer', () => {
                el['footer'] = view.model.get('footer');
            });

            view.model.on('change:stac_info', () => {
                el['stacInfo'] = view.model.get('stac_info');
            });

            view.model.on('change:stac_properties', () => {
                el['stacProperties'] = view.model.get('stac_properties');
            });
                
                // Add Method Listener
                
                view.model.on("msg:custom", (content) => {
                    if (content.type === "call_method") {
                        const methodName = content.name;
                        const args = content.args;
                        if (typeof el[methodName] === 'function') {
                            el[methodName](...args);
                        }
                    }
                });
    

                view.el.appendChild(el);
            }

            init();
        }
    }
    """


    def __init__(self, version="latest", **kwargs):
        imports = []
        # Dependencies
        imports.extend([])
        
        # Dynamic imports
        pkg_name = "stacinfo"
        
        # Extra imports
        extra_paths = []
        for path in extra_paths:
            imports.append(f"https://cdn.jsdelivr.net/npm/@eox/{pkg_name}@{version}/{path}")
            
        # Main import
        imports.append(f"https://cdn.jsdelivr.net/npm/@eox/{pkg_name}@{version}/dist/eox-stacinfo.js")
        
        imports_str = "\n    ".join([f'import "{url}";' for url in imports])
        
        kwargs['_esm'] = self._esm_template.replace("{imports_str}", imports_str)
        
        super().__init__(**kwargs)
    

    id = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    allow_html = traitlets.Bool(False).tag(sync=True)
    unstyled = traitlets.Bool(False).tag(sync=True)
    for_ = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    header = traitlets.List(None, allow_none=True).tag(sync=True)
    tags = traitlets.List(None, allow_none=True).tag(sync=True)
    body = traitlets.List(None, allow_none=True).tag(sync=True)
    featured = traitlets.List(None, allow_none=True).tag(sync=True)
    footer = traitlets.List(None, allow_none=True).tag(sync=True)
    stac_info = traitlets.List(None, allow_none=True).tag(sync=True)
    stac_properties = traitlets.List(None, allow_none=True).tag(sync=True)



class EOxTimecontrol(anywidget.AnyWidget, DOMWidget):
    """The `eox-timecontrol` element provides interactive time navigation for map layers, supporting animation, a simple time slider, timeline visualization, date picker, and custom date formatting.

## Basic usage:

```
import "@eox/timecontrol"

<eox-timecontrol for="eox-map#my-map">
  <eox-timecontrol-date></eox-timecontrol-date>
  <eox-timecontrol-slider></eox-timecontrol-slider>
  <eox-timecontrol-timeline></eox-timecontrol-timeline>
  <eox-timecontrol-timelapse></eox-timecontrol-timelapse>
  <eox-timecontrol-picker></eox-timecontrol-picker>
</eox-timecontrol>
```

## Features

- **Time-based Layer Control:** Link to an `<eox-map>` instance for time-based WMS layer control. Automatically detects layers with `timeControlValues` and `timeControlProperty` properties.
- **Multiple UI Components:** Supports date display, date picker (popup or inline), timeline visualization, slider, and timelapse export.
- **Navigation Controls:** Previous/next buttons for stepping through time periods.
- **Date Formatting:** Customizable display format using dayjs tokens (default: "YYYY-MM-DD").
- **Filtering:** Integration with `<eox-itemfilter>` for filtering timeline items by metadata properties.
- **Timelapse Export:** Export animated GIFs or MP4s from time series data.
- **Standalone Mode:** Can be used without a map for time selection purposes.

## Component Structure

The timecontrol element acts as a container for child components:
- `<eox-timecontrol-date>`: Displays the current selected date(s) with optional navigation buttons.
- `<eox-timecontrol-picker>`: Calendar-based date picker (popup or inline, single or range selection).
- `<eox-timecontrol-slider>`: Range slider for selecting date ranges.
- `<eox-timecontrol-timeline>`: Timeline visualization using vis-timeline.
- `<eox-timecontrol-timelapse>`: Timelapse export functionality.

## Layer Configuration

Layers must have the following properties to work with timecontrol:
- `properties.timeControlValues`: Array of objects with `date` and optional metadata.
- `properties.timeControlProperty`: Property name used in WMS requests (e.g., "TIME").
- `properties.id`: Layer identifier (used for grouping in timeline).
- `properties.name`: Display name (used in timeline groups).

## Events

- `stepchange`: Fired when the current time step changes (not currently implemented)."""
    _esm = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    _esm_template = """
    {imports_str}

    export default {
        render(view) {
            const tag_name = 'eox-timecontrol';
            
            function init() {
                if (view.el.querySelector(tag_name)) return;
                const el = document.createElement(tag_name);
                el.style.width = "100%";
                el.style.height = "100%";

                // Apply Properties
                
        const id = view.model.get('id');
        if (id !== null) { el.id = id; }
    

            {
                const slider_values = view.model.get('slider_values');
                if (slider_values !== null) {
                    el['sliderValues'] = slider_values;
                }
            }

            {
                const eox_map = view.model.get('eox_map');
                if (eox_map !== null) {
                    el['eoxMap'] = eox_map;
                }
            }

            {
                const groups = view.model.get('groups');
                if (groups !== null) {
                    el['groups'] = groups;
                }
            }

            {
                const items = view.model.get('items');
                if (items !== null) {
                    el['items'] = items;
                }
            }

            {
                const date_change = view.model.get('date_change');
                if (date_change !== null) {
                    el['dateChange'] = date_change;
                }
            }

            {
                const filter = view.model.get('filter');
                if (filter !== null) {
                    el['filter'] = filter;
                }
            }

            {
                const unstyled = view.model.get('unstyled');
                if (unstyled !== null) {
                    el['unstyled'] = unstyled;
                }
            }

            {
                const selected_date_range = view.model.get('selected_date_range');
                if (selected_date_range !== null) {
                    el['selectedDateRange'] = selected_date_range;
                }
            }

            {
                const title_key = view.model.get('title_key');
                if (title_key !== null) {
                    el['titleKey'] = title_key;
                }
            }

            {
                const layer_id_key = view.model.get('layer_id_key');
                if (layer_id_key !== null) {
                    el['layerIdKey'] = layer_id_key;
                }
            }

            {
                const external_map_rendering = view.model.get('external_map_rendering');
                if (external_map_rendering !== null) {
                    el['externalMapRendering'] = external_map_rendering;
                }
            }

            {
                const for_ = view.model.get('for_');
                if (for_ !== null) {
                    const checkExist = setInterval(() => {
                       if (document.querySelector(for_)) {
                          el['for'] = for_;
                          clearInterval(checkExist);
                       }
                    }, 100);
                    setTimeout(() => clearInterval(checkExist), 10000);
                }
            }

            {
                const control_values = view.model.get('control_values');
                if (control_values !== null) {
                    el['controlValues'] = control_values;
                }
            }

            {
                const init_date = view.model.get('init_date');
                if (init_date !== null) {
                    el['initDate'] = init_date;
                }
            }

                // Add Listeners
                
        view.model.on('change:id', () => { el.id = view.model.get('id'); });
    

            view.model.on('change:slider_values', () => {
                el['sliderValues'] = view.model.get('slider_values');
            });

            view.model.on('change:eox_map', () => {
                el['eoxMap'] = view.model.get('eox_map');
            });

            view.model.on('change:groups', () => {
                el['groups'] = view.model.get('groups');
            });

            view.model.on('change:items', () => {
                el['items'] = view.model.get('items');
            });

            view.model.on('change:date_change', () => {
                el['dateChange'] = view.model.get('date_change');
            });

            view.model.on('change:filter', () => {
                el['filter'] = view.model.get('filter');
            });

            view.model.on('change:unstyled', () => {
                el['unstyled'] = view.model.get('unstyled');
            });

            view.model.on('change:selected_date_range', () => {
                el['selectedDateRange'] = view.model.get('selected_date_range');
            });

            view.model.on('change:title_key', () => {
                el['titleKey'] = view.model.get('title_key');
            });

            view.model.on('change:layer_id_key', () => {
                el['layerIdKey'] = view.model.get('layer_id_key');
            });

            view.model.on('change:external_map_rendering', () => {
                el['externalMapRendering'] = view.model.get('external_map_rendering');
            });

            view.model.on('change:for_', () => {
                const val = view.model.get('for_');
                const checkExist = setInterval(() => {
                   if (document.querySelector(val)) {
                      el['for'] = val;
                      clearInterval(checkExist);
                   }
                }, 100);
                setTimeout(() => clearInterval(checkExist), 10000);
            });

            view.model.on('change:control_values', () => {
                el['controlValues'] = view.model.get('control_values');
            });

            view.model.on('change:init_date', () => {
                el['initDate'] = view.model.get('init_date');
            });
                
                // Add Method Listener
                
                view.model.on("msg:custom", (content) => {
                    if (content.type === "call_method") {
                        const methodName = content.name;
                        const args = content.args;
                        if (typeof el[methodName] === 'function') {
                            el[methodName](...args);
                        }
                    }
                });
    

                view.el.appendChild(el);
            }

            
            const check = setInterval(() => {
                if (document.querySelector('eox-map')) {
                    clearInterval(check);
                    init();
                }
            }, 100);
            setTimeout(() => {
                if (check) clearInterval(check);
                if (!view.el.querySelector(tag_name)) init(); 
            }, 5000);
        
        }
    }
    """


    def __init__(self, version="latest", **kwargs):
        imports = []
        # Dependencies
        imports.extend([])
        
        # Dynamic imports
        pkg_name = "timecontrol"
        
        # Extra imports
        extra_paths = []
        for path in extra_paths:
            imports.append(f"https://cdn.jsdelivr.net/npm/@eox/{pkg_name}@{version}/{path}")
            
        # Main import
        imports.append(f"https://cdn.jsdelivr.net/npm/@eox/{pkg_name}@{version}/dist/eox-timecontrol.js")
        
        imports_str = "\n    ".join([f'import "{url}";' for url in imports])
        
        kwargs['_esm'] = self._esm_template.replace("{imports_str}", imports_str)
        
        super().__init__(**kwargs)
    

    id = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    slider_values = traitlets.List(None, allow_none=True).tag(sync=True)
    eox_map = traitlets.Any(None, allow_none=True).tag(sync=True)
    groups = traitlets.Any(None, allow_none=True).tag(sync=True)
    items = traitlets.Any(None, allow_none=True).tag(sync=True)
    date_change = traitlets.Any(None, allow_none=True).tag(sync=True)
    filter = traitlets.Any(None, allow_none=True).tag(sync=True)
    unstyled = traitlets.Bool(False).tag(sync=True)
    selected_date_range = traitlets.Any(None, allow_none=True).tag(sync=True)
    title_key = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    layer_id_key = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    external_map_rendering = traitlets.Bool(False).tag(sync=True)
    for_ = traitlets.Any(None, allow_none=True).tag(sync=True)
    control_values = traitlets.List(None, allow_none=True).tag(sync=True)
    init_date = traitlets.Any(None, allow_none=True).tag(sync=True)

    def get_container(self, ):
        """
        Calls the 'getContainer' method on the web component.
        """
        self.send({
            "type": "call_method",
            "name": "getContainer",
            "args": []
        })
        

    def get_time_control_date(self, ):
        """
        Calls the 'getTimeControlDate' method on the web component.
        """
        self.send({
            "type": "call_method",
            "name": "getTimeControlDate",
            "args": []
        })
        

    def get_time_control_slider(self, ):
        """
        Calls the 'getTimeControlSlider' method on the web component.
        """
        self.send({
            "type": "call_method",
            "name": "getTimeControlSlider",
            "args": []
        })
        

    def get_time_control_timeline(self, ):
        """
        Calls the 'getTimeControlTimeline' method on the web component.
        """
        self.send({
            "type": "call_method",
            "name": "getTimeControlTimeline",
            "args": []
        })
        

    def get_time_control_timelapse(self, ):
        """
        Calls the 'getTimeControlTimelapse' method on the web component.
        """
        self.send({
            "type": "call_method",
            "name": "getTimeControlTimelapse",
            "args": []
        })
        

    def get_time_control_picker(self, ):
        """
        Calls the 'getTimeControlPicker' method on the web component.
        """
        self.send({
            "type": "call_method",
            "name": "getTimeControlPicker",
            "args": []
        })
        
