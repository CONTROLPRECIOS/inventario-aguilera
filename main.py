import json
import os
import urllib.parse
import webbrowser
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput

ARCHIVO_DATOS = "inventario_aguilera.json"

CATEGORIAS_DISPONIBLES = [
    "1. Víveres",
    "2. Charcutería",
]


class InventarioApp(App):

  def build(self):
    self.title = "COMERCIALIZADORA HNOS. AGUILERA 2019 C.A"
    self.tasa_bcv = 690.12
    self.productos = []
    self.combos_guardados = []
    self.items_combo_temp = []
    self.vista_actual = "productos"

    # Cargar datos guardados previamente en el teléfono
    self.cargar_datos_disco()

    # Layout Principal con buen espaciado
    main_layout = BoxLayout(orientation="vertical", padding=12, spacing=10)

    # Encabezado Comercial
    header = Label(
        text=(
            "[b]COMERCIALIZADORA HNOS. AGUILERA 2019 C.A[/b]\nRIF:"
            " J-41283366-9"
        ),
        markup=True,
        size_hint_y=None,
        height=60,
        halign="center",
        valign="middle",
    )
    header.bind(size=header.setter("text_size"))
    main_layout.add_widget(header)

    # Panel Tasa BCV
    bcv_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
    bcv_layout.add_widget(
        Label(text="Tasa BCV (Bs):", size_hint_x=0.35, bold=True)
    )
    self.input_bcv = TextInput(
        text=str(self.tasa_bcv),
        multiline=False,
        input_filter="float",
        size_hint_x=0.35,
    )
    btn_set_bcv = Button(
        text="Actualizar",
        size_hint_x=0.3,
        background_color=(0.2, 0.6, 1, 1),
    )
    btn_set_bcv.bind(on_press=self.actualizar_tasa)
    bcv_layout.add_widget(self.input_bcv)
    bcv_layout.add_widget(btn_set_bcv)
    main_layout.add_widget(bcv_layout)

    # Botones Principales de Acción
    action_layout = GridLayout(cols=2, size_hint_y=None, height=130, spacing=8)

    btn_add_prod = Button(
        text="+ Agregar Producto", background_color=(0.3, 0.8, 0.3, 1)
    )
    btn_add_prod.bind(on_press=self.abrir_popup_producto)

    btn_ver_prods = Button(
        text="Ver Productos", background_color=(0.2, 0.4, 0.8, 1)
    )
    btn_ver_prods.bind(on_press=self.mostrar_productos)

    btn_crear_combo = Button(
        text="+ Crear Combo / WA", background_color=(1, 0.6, 0.2, 1)
    )
    btn_crear_combo.bind(on_press=self.abrir_creador_combo)

    btn_ver_combos = Button(
        text="Ver Combos Guardados", background_color=(0.8, 0.3, 0.8, 1)
    )
    btn_ver_combos.bind(on_press=self.mostrar_combos_guardados)

    action_layout.add_widget(btn_add_prod)
    action_layout.add_widget(btn_ver_prods)
    action_layout.add_widget(btn_crear_combo)
    action_layout.add_widget(btn_ver_combos)
    main_layout.add_widget(action_layout)

    # Área de Visualización con Scroll
    self.scroll = ScrollView()
    self.pantalla_contenido = GridLayout(cols=1, spacing=15, size_hint_y=None)
    self.pantalla_contenido.bind(
        minimum_height=self.pantalla_contenido.setter("height")
    )
    self.scroll.add_widget(self.pantalla_contenido)
    main_layout.add_widget(self.scroll)

    self.mostrar_productos(None)
    return main_layout

  # --- PERSISTENCIA Y SINCRONIZACIÓN DE PRECIOS ---
  def guardar_datos_disco(self):
    try:
      self.actualizar_totales_combos()
      datos = {
          "tasa_bcv": self.tasa_bcv,
          "productos": self.productos,
          "combos_guardados": self.combos_guardados,
      }
      with open(ARCHIVO_DATOS, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)
    except Exception as e:
      print("Error al guardar:", e)

  def cargar_datos_disco(self):
    if os.path.exists(ARCHIVO_DATOS):
      try:
        with open(ARCHIVO_DATOS, "r", encoding="utf-8") as f:
          datos = json.load(f)
          self.tasa_bcv = datos.get("tasa_bcv", 690.12)
          self.productos = datos.get("productos", [])
          self.combos_guardados = datos.get("combos_guardados", [])

          for p in self.productos:
            if "categoria" not in p:
              p["categoria"] = "1. Víveres"

          self.actualizar_totales_combos()
      except Exception as e:
        print("Error al cargar:", e)

  def actualizar_totales_combos(self):
    """Recalcula estrictamente el total USD y sincroniza los precios frescos de cada combo"""
    for c in self.combos_guardados:
      total_usd = 0.0
      for it in c["items"]:
        nombre_buscado = it["prod"]["nombre"]
        prod_actualizado = next(
            (
                p
                for p in self.productos
                if p["nombre"].upper() == nombre_buscado.upper()
            ),
            None,
        )
        if prod_actualizado:
          it["prod"] = prod_actualizado
          total_usd += prod_actualizado["precio_unit_usd"] * it["cantidad"]
        else:
          total_usd += (
              it["prod"].get("precio_unit_usd", 0.0) * it["cantidad"]
          )
      c["total_usd"] = total_usd

  # --- GESTIÓN DE TASA ---
  def actualizar_tasa(self, instance):
    try:
      val = float(self.input_bcv.text)
      if val > 0:
        self.tasa_bcv = val
        self.actualizar_totales_combos()
        self.guardar_datos_disco()

        # Refrescar la pantalla activa al instante
        if self.vista_actual == "combos":
          self.mostrar_combos_guardados(None)
        else:
          self.mostrar_productos(None)

        self.mostrar_notificacion(
            "Éxito",
            f"Tasa BCV actualizada a {val} Bs.\nPrecios en $ y Bs recalculados.",
        )
    except ValueError:
      self.mostrar_notificacion("Error", "Ingrese un valor numérico válido.")

  # --- AGREGAR O EDITAR PRODUCTO ---
  def abrir_popup_producto(
      self, instance, producto_existente=None, index_existente=None
  ):
    es_edicion = producto_existente is not None

    content = BoxLayout(
        orientation="vertical", spacing=12, padding=15, size_hint_y=None
    )
    content.bind(minimum_height=content.setter("height"))

    titulo_popup = "Editar Producto" if es_edicion else "Registrar Nuevo Producto"
    content.add_widget(
        Label(
            text=f"[b]{titulo_popup}[/b]",
            markup=True,
            size_hint_y=None,
            height=35,
        )
    )

    content.add_widget(
        Label(
            text="Seleccione Bloque (Sección):",
            size_hint_y=None,
            height=25,
            halign="left",
        )
    )
    cat_inicial = (
        producto_existente.get("categoria", CATEGORIAS_DISPONIBLES[0])
        if es_edicion
        else CATEGORIAS_DISPONIBLES[0]
    )
    spinner_cat = Spinner(
        text=cat_inicial,
        values=tuple(CATEGORIAS_DISPONIBLES),
        size_hint_y=None,
        height=50,
    )
    content.add_widget(spinner_cat)

    content.add_widget(
        Label(
            text="Nombre del Producto:",
            size_hint_y=None,
            height=25,
            halign="left",
        )
    )
    input_nombre = TextInput(
        text=str(producto_existente.get("nombre", "")) if es_edicion else "",
        hint_text="Ej: Arroz / Harina Pan / Queso",
        multiline=False,
        size_hint_y=None,
        height=50,
    )
    content.add_widget(input_nombre)

    content.add_widget(
        Label(
            text="Costo total del empaque ($):",
            size_hint_y=None,
            height=25,
            halign="left",
        )
    )
    input_costo = TextInput(
        text=str(producto_existente.get("costo_pack", "")) if es_edicion else "",
        hint_text="Ej: 15.50",
        multiline=False,
        input_filter="float",
        size_hint_y=None,
        height=50,
    )
    content.add_widget(input_costo)

    content.add_widget(
        Label(
            text="Cantidad de unidades en el empaque:",
            size_hint_y=None,
            height=25,
            halign="left",
        )
    )
    input_cant = TextInput(
        text=str(producto_existente.get("cantidad", "")) if es_edicion else "",
        hint_text="Ej: 20",
        multiline=False,
        input_filter="int",
        size_hint_y=None,
        height=50,
    )
    content.add_widget(input_cant)

    content.add_widget(
        Label(
            text="Seleccione Porcentaje de Ganancia:",
            size_hint_y=None,
            height=25,
            halign="left",
        )
    )
    margen_inicial = (
        f"{producto_existente.get('margen_pct', '30')}%"
        if es_edicion
        else "30%"
    )
    spinner_margen = Spinner(
        text=margen_inicial,
        values=("15%", "25%", "30%", "35%", "70%"),
        size_hint_y=None,
        height=50,
    )
    content.add_widget(spinner_margen)

    texto_boton = "Guardar Cambios" if es_edicion else "Guardar Producto"
    btn_guardar = Button(
        text=texto_boton,
        size_hint_y=None,
        height=55,
        background_color=(0.3, 0.8, 0.3, 1),
    )
    content.add_widget(btn_guardar)

    scroll_p = ScrollView(size_hint=(1, 1))
    scroll_p.add_widget(content)

    popup = Popup(
        title=titulo_popup,
        content=scroll_p,
        size_hint=(0.95, 0.90),
        auto_dismiss=True,
    )

    def guardar_prod(btn_inst):
      try:
        categoria = spinner_cat.text
        nombre = input_nombre.text.strip()
        costo = float(input_costo.text)
        cant = int(input_cant.text)
        margen_str = spinner_margen.text.replace("%", "")
        margen = float(margen_str) / 100.0

        if not nombre or costo <= 0 or cant <= 0:
          self.mostrar_notificacion(
              "Atención", "Rellene todos los campos correctamente."
          )
          return

        costo_unitario = costo / cant
        precio_venta_unit_usd = costo_unitario * (1 + margen)

        prod = {
            "categoria": categoria,
            "nombre": nombre,
            "costo_pack": costo,
            "cantidad": cant,
            "costo_unitario": costo_unitario,
            "margen_pct": margen_str,
            "precio_unit_usd": precio_venta_unit_usd,
        }

        if es_edicion:
          self.productos[index_existente] = prod
        else:
          self.productos.append(prod)

        self.guardar_datos_disco()
        popup.dismiss()

        if self.vista_actual == "combos":
          self.mostrar_combos_guardados(None)
        else:
          self.mostrar_productos(None)
      except ValueError:
        self.mostrar_notificacion(
            "Error", "Verifique que los números sean correctos."
        )

    btn_guardar.bind(on_press=guardar_prod)
    popup.open()

  # --- MOSTRAR LISTA GENERAL ---
  def mostrar_productos(self, instance):
    self.vista_actual = "productos"
    self.pantalla_contenido.clear_widgets()

    if not self.productos:
      self.pantalla_contenido.add_widget(
          Label(
              text="No hay productos registrados.",
              size_hint_y=None,
              height=40,
          )
      )
      return

    header_text = Label(
        text=(
            "[b]--- INVENTARIO GENERAL ---[/b]\n[i](Use el botón [ Editar ] para"
            " modificar un producto)[/i]"
        ),
        markup=True,
        size_hint_y=None,
        height=50,
        halign="center",
        valign="middle",
    )
    header_text.bind(size=lambda s, w: setattr(s, "text_size", (w[0], None)))
    self.pantalla_contenido.add_widget(header_text)

    productos_ordenados = sorted(
        self.productos,
        key=lambda x: 0 if "1." in x.get("categoria", "") else 1,
    )

    viveres_marcado = False
    charcuteria_marcada = False

    for p in productos_ordenados:
      idx = self.productos.index(p)
      categoria_p = p.get("categoria", "1. Víveres")

      if "1." in categoria_p and not viveres_marcado:
        viveres_marcado = True
        lbl_viv = Label(
            text="[b][color=ffaa00]📂 VÍVERES[/color][/b]",
            markup=True,
            size_hint_y=None,
            height=35,
            halign="left",
            valign="middle",
        )
        lbl_viv.bind(size=lambda s, w: setattr(s, "text_size", (w[0], None)))
        self.pantalla_contenido.add_widget(lbl_viv)

      if "2." in categoria_p and not charcuteria_marcada:
        charcuteria_marcada = True
        lbl_charc_aviso = Label(
            text="[color=ffff00][b]=== 🌟 CHARCUTERIA ===[/b][/color]",
            markup=True,
            size_hint_y=None,
            height=45,
            halign="left",
            valign="middle",
        )
        lbl_charc_aviso.bind(
            size=lambda s, w: setattr(s, "text_size", (w[0], None))
        )
        self.pantalla_contenido.add_widget(lbl_charc_aviso)

      precio_bs = p["precio_unit_usd"] * self.tasa_bcv

      box = BoxLayout(
          orientation="horizontal",
          size_hint_y=None,
          height=115,
          spacing=5,
          padding=6,
      )

      text_box = BoxLayout(orientation="vertical", size_hint_x=0.68, spacing=3)

      lbl_nombre = Label(
          text=f"[b]• {p['nombre'].upper()}[/b]",
          markup=True,
          size_hint_y=None,
          height=30,
          halign="left",
          valign="middle",
      )
      lbl_nombre.bind(
          size=lambda s, w: setattr(s, "text_size", (w[0], None))
      )

      lbl_detalles = Label(
          text=(
              f"Empaque: {p['cantidad']} un. | Ganancia: {p['margen_pct']}%"
          ),
          size_hint_y=None,
          height=25,
          halign="left",
          valign="middle",
      )
      lbl_detalles.bind(
          size=lambda s, w: setattr(s, "text_size", (w[0], None))
      )

      lbl_precio = Label(
          text=(
              f"Venta Unit: [b]${p['precio_unit_usd']:.2f}[/b] /"
              f" [color=00ff00]{precio_bs:,.2f} Bs[/color]"
          ),
          markup=True,
          size_hint_y=None,
          height=30,
          halign="left",
          valign="middle",
      )
      lbl_precio.bind(size=lambda s, w: setattr(s, "text_size", (w[0], None)))

      text_box.add_widget(lbl_nombre)
      text_box.add_widget(lbl_detalles)
      text_box.add_widget(lbl_precio)

      btn_edit = Button(
          text="Editar",
          size_hint_x=0.18,
          background_color=(0.2, 0.6, 1, 1),
          font_size=13,
      )
      btn_edit.bind(
          on_press=lambda inst, prod=p, i=idx: self.abrir_popup_producto(
              None, producto_existente=prod, index_existente=i
          )
      )

      btn_del = Button(
          text="X",
          size_hint_x=0.14,
          background_color=(1, 0.3, 0.3, 1),
          font_size=16,
      )
      btn_del.bind(
          on_press=lambda inst, i=idx: self.confirmar_eliminacion_producto(i)
      )

      box.add_widget(text_box)
      box.add_widget(btn_edit)
      box.add_widget(btn_del)
      self.pantalla_contenido.add_widget(box)

  def confirmar_eliminacion_producto(self, index):
    if not (0 <= index < len(self.productos)):
      return
    prod_nombre = self.productos[index]["nombre"]

    content = BoxLayout(orientation="vertical", padding=15, spacing=15)
    content.add_widget(
        Label(
            text=(
                f"¿Está seguro de eliminar el producto:\n[b]{prod_nombre}[/b]?"
            ),
            markup=True,
            halign="center",
        )
    )

    btn_box = BoxLayout(size_hint_y=None, height=45, spacing=10)
    btn_si = Button(text="Sí, eliminar", background_color=(1, 0.3, 0.3, 1))
    btn_no = Button(text="Cancelar", background_color=(0.5, 0.5, 0.5, 1))
    btn_box.add_widget(btn_si)
    btn_box.add_widget(btn_no)
    content.add_widget(btn_box)

    popup = Popup(
        title="Confirmar Eliminación",
        content=content,
        size_hint=(0.8, 0.35),
        auto_dismiss=True,
    )

    def eliminar(instance):
      del self.productos[index]
      self.guardar_datos_disco()
      if self.vista_actual == "combos":
        self.mostrar_combos_guardados(None)
      else:
        self.mostrar_productos(None)
      popup.dismiss()

    btn_si.bind(on_press=eliminar)
    btn_no.bind(on_press=popup.dismiss)
    popup.open()

  # --- CREADOR DE COMBOS CUSTOM / WHATSAPP ---
  def abrir_creador_combo(self, instance):
    if not self.productos:
      self.mostrar_notificacion(
          "Atención", "Primero agregue productos a la lista."
      )
      return

    self.items_combo_temp = []
    content = BoxLayout(
        orientation="vertical", spacing=10, padding=12, size_hint_y=None
    )
    content.bind(minimum_height=content.setter("height"))

    content.add_widget(
        Label(
            text="[b]Diseñador de Combo Custom[/b]",
            markup=True,
            size_hint_y=None,
            height=30,
        )
    )

    content.add_widget(
        Label(
            text="Nombre del Combo:",
            size_hint_y=None,
            height=22,
            halign="left",
        )
    )
    input_nombre_combo = TextInput(
        hint_text="Ej: COMBO BASICO",
        multiline=False,
        size_hint_y=None,
        height=45,
    )
    content.add_widget(input_nombre_combo)

    content.add_widget(
        Label(
            text="Seleccione Producto:",
            size_hint_y=None,
            height=22,
            halign="left",
        )
    )
    nombres_prods = [p["nombre"] for p in self.productos]
    spinner_prod = Spinner(
        text=nombres_prods[0] if nombres_prods else "",
        values=nombres_prods,
        size_hint_y=None,
        height=45,
    )
    content.add_widget(spinner_prod)

    content.add_widget(
        Label(
            text="Cantidad en el combo:",
            size_hint_y=None,
            height=22,
            halign="left",
        )
    )
    input_cant_item = TextInput(
        hint_text="Ej: 2",
        multiline=False,
        input_filter="int",
        size_hint_y=None,
        height=45,
    )
    content.add_widget(input_cant_item)

    btn_add_item = Button(
        text="+ Añadir producto al combo",
        size_hint_y=None,
        height=45,
        background_color=(0.2, 0.7, 0.9, 1),
    )
    content.add_widget(btn_add_item)

    content.add_widget(
        Label(
            text="[b]Productos en este combo:[/b]",
            markup=True,
            size_hint_y=None,
            height=25,
            halign="left",
        )
    )

    scroll_items = ScrollView(size_hint_y=None, height=190)
    lista_items_temp = GridLayout(cols=1, spacing=8, size_hint_y=None)
    lista_items_temp.bind(
        minimum_height=lista_items_temp.setter("height")
    )
    scroll_items.add_widget(lista_items_temp)
    content.add_widget(scroll_items)

    lbl_resumen = Label(
        text="Total: $0.00 (0.00 Bs)", size_hint_y=None, height=35, bold=True
    )
    content.add_widget(lbl_resumen)

    btn_box = BoxLayout(size_hint_y=None, height=50, spacing=8)
    btn_guardar_combo = Button(
        text="Guardar Combo", background_color=(0.8, 0.4, 0.8, 1)
    )
    btn_enviar_wa = Button(
        text="Enviar WhatsApp", background_color=(0.2, 0.8, 0.4, 1)
    )
    btn_box.add_widget(btn_guardar_combo)
    btn_box.add_widget(btn_enviar_wa)
    content.add_widget(btn_box)

    scroll_c = ScrollView(size_hint=(1, 1))
    scroll_c.add_widget(content)

    popup = Popup(
        title="Crear Combo Personalizado",
        content=scroll_c,
        size_hint=(0.95, 0.95),
        auto_dismiss=True,
    )

    def actualizar_vista_combo_temp():
      lista_items_temp.clear_widgets()
      tot = 0.0

      if not self.items_combo_temp:
        lista_items_temp.add_widget(
            Label(
                text="Ningún producto agregado todavía.",
                size_hint_y=None,
                height=35,
            )
        )
      else:
        for index_it, item in enumerate(self.items_combo_temp):
          p = item["prod"]
          subtotal = p["precio_unit_usd"] * item["cantidad"]
          tot += subtotal

          row_box = BoxLayout(
              orientation="horizontal",
              size_hint_y=None,
              height=75,
              spacing=6,
              padding=4,
          )

          item_text_box = BoxLayout(
              orientation="vertical", size_hint_x=0.75, spacing=2
          )

          lbl_nombre_it = Label(
              text=f"[b]{item['cantidad']}x {p['nombre']}[/b]",
              markup=True,
              size_hint_y=None,
              height=35,
              halign="left",
              valign="middle",
          )
          lbl_nombre_it.bind(
              size=lambda s, w: setattr(s, "text_size", (w[0], None))
          )

          lbl_sub_it = Label(
              text=f"Subtotal: ${subtotal:.2f}",
              size_hint_y=None,
              height=30,
              halign="left",
              valign="middle",
          )
          lbl_sub_it.bind(
              size=lambda s, w: setattr(s, "text_size", (w[0], None))
          )

          item_text_box.add_widget(lbl_nombre_it)
          item_text_box.add_widget(lbl_sub_it)

          btn_del_it = Button(
              text="X", size_hint_x=0.25, background_color=(1, 0.3, 0.3, 1)
          )
          btn_del_it.bind(
              on_press=lambda inst, idx=index_it: eliminar_item_temp(idx)
          )

          row_box.add_widget(item_text_box)
          row_box.add_widget(btn_del_it)
          lista_items_temp.add_widget(row_box)

      tot_bs = tot * self.tasa_bcv
      lbl_resumen.text = f"Total: ${tot:.2f} ({tot_bs:,.2f} Bs)"

    def eliminar_item_temp(idx):
      if 0 <= idx < len(self.items_combo_temp):
        del self.items_combo_temp[idx]
        actualizar_vista_combo_temp()

    def agregar_item(b_inst):
      p_nombre = spinner_prod.text
      try:
        qty_text = input_cant_item.text.replace("Ei: ", "").strip()
        qty = int(qty_text)
        prod_obj = next(
            (p for p in self.productos if p["nombre"] == p_nombre), None
        )
        if prod_obj and qty > 0:
          self.items_combo_temp.append({"prod": prod_obj, "cantidad": qty})
          input_cant_item.text = ""
          actualizar_vista_combo_temp()
      except ValueError:
        self.mostrar_notificacion(
            "Error", "Ingrese una cantidad numérica válida."
        )

    def calcular_total_temp():
      return sum(
          item["prod"]["precio_unit_usd"] * item["cantidad"]
          for item in self.items_combo_temp
      )

    def guardar_combo(b_inst):
      nombre = (
          input_nombre_combo.text.strip()
          or f"Combo #{len(self.combos_guardados)+1}"
      )
      tot_usd = calcular_total_temp()
      if self.items_combo_temp:
        combo_obj = {
            "nombre": nombre,
            "items": list(self.items_combo_temp),
            "total_usd": tot_usd,
        }
        self.combos_guardados.append(combo_obj)
        self.guardar_datos_disco()
        popup.dismiss()
        self.mostrar_notificacion(
            "Éxito", f"Combo '{nombre}' guardado correctamente."
        )
      else:
        self.mostrar_notificacion(
            "Atención", "Debe agregar al menos un producto al combo."
        )

    def enviar_whatsapp(b_inst):
      if not self.items_combo_temp:
        self.mostrar_notificacion(
            "Atención", "Agregue productos antes de enviar por WhatsApp."
        )
        return

      nombre_c = input_nombre_combo.text.strip() or "Combo Especial"
      tot_usd = calcular_total_temp()
      tot_bs = tot_usd * self.tasa_bcv

      msg = f"*COMERCIALIZADORA HNOS. AGUILERA 2019 C.A*\n"
      msg += f"*RIF: J-41283366-9*\n"
      msg += f"*Presupuesto: {nombre_c}*\n\n"
      msg += "Detalle del combo:\n"

      for it in self.items_combo_temp:
        p = it["prod"]
        sub_usd = p["precio_unit_usd"] * it["cantidad"]
        sub_bs = sub_usd * self.tasa_bcv
        msg += f"• {it['cantidad']}x {p['nombre']} - ${sub_usd:.2f} ({sub_bs:,.2f} Bs)\n"

      msg += f"\n*TOTAL: ${tot_usd:.2f} / {tot_bs:,.2f} Bs*\n"
      msg += f"(Tasa BCV: {self.tasa_bcv} Bs/$)\n\n"
      msg += "¡Estamos a su orden para procesar su pedido!"

      numero = "+584245389751"
      msg_encoded = urllib.parse.quote(msg)
      url = f"https://wa.me/{numero}?text={msg_encoded}"

      webbrowser.open(url)
      popup.dismiss()

    btn_add_item.bind(on_press=agregar_item)
    btn_guardar_combo.bind(on_press=guardar_combo)
    btn_enviar_wa.bind(on_press=enviar_whatsapp)

    actualizar_vista_combo_temp()
    popup.open()

  # --- MOSTRAR COMBOS GUARDADOS (UN SOLO BLOQUE LIMPIO DE TEXTO Y ALTURA DINÁMICA PERFECTA) ---
  def mostrar_combos_guardados(self, instance):
    self.vista_actual = "combos"
    self.pantalla_contenido.clear_widgets()

    # Recalcular totales USD frescos de los productos actuales
    self.actualizar_totales_combos()

    if not self.combos_guardados:
      self.pantalla_contenido.add_widget(
          Label(
              text="No hay combos guardados.", size_hint_y=None, height=40
          )
      )
      return

    header_text = Label(
        text="[b]--- COMBOS GUARDADOS ---[/b]",
        markup=True,
        size_hint_y=None,
        height=35,
    )
    self.pantalla_contenido.add_widget(header_text)

    for idx, c in enumerate(self.combos_guardados):
      precio_bs = c["total_usd"] * self.tasa_bcv
      num_articulos = len(c["items"])

      # Altura generosa calculada según la cantidad de artículos para que jamás se encimen
      altura_tarjeta = 110 + (num_articulos * 28)

      box = BoxLayout(
          orientation="vertical",
          size_hint_y=None,
          height=altura_tarjeta,
          padding=10,
          spacing=4,
      )

      lbl_nombre = Label(
          text=f"[b]🎁 {c['nombre'].upper()}[/b]",
          markup=True,
          size_hint_y=None,
          height=28,
          halign="left",
          valign="middle",
      )
      lbl_nombre.bind(
          size=lambda s, w: setattr(s, "text_size", (w[0], None))
      )

      # Construir un único texto multilinea para todos los ítems (Cero solapamiento)
      texto_lista_items = ""
      for it in c["items"]:
        prod_ref = next(
            (
                p
                for p in self.productos
                if p["nombre"].upper() == it["prod"]["nombre"].upper()
            ),
            it["prod"],
        )
        sub_usd = prod_ref["precio_unit_usd"] * it["cantidad"]
        sub_bs = sub_usd * self.tasa_bcv
        texto_lista_items += (
            f"• {it['cantidad']}x {prod_ref['nombre']} "
            f"[color=ffcc00](${sub_usd:.2f} / {sub_bs:,.2f} Bs)[/color]\n"
        )

      lbl_items_block = Label(
          text=texto_lista_items.strip(),
          markup=True,
          size_hint_y=None,
          height=num_articulos * 26,
          halign="left",
          valign="top",
          font_size=13,
      )
      lbl_items_block.bind(
          size=lambda s, w: setattr(s, "text_size", (w[0], None))
      )

      lbl_precio = Label(
          text=(
              f"Total Combo: [b]${c['total_usd']:.2f}[/b] /"
              f" [color=00ff00]{precio_bs:,.2f} Bs[/color]"
          ),
          markup=True,
          size_hint_y=None,
          height=32,
          halign="left",
          valign="middle",
      )
      lbl_precio.bind(size=lambda s, w: setattr(s, "text_size", (w[0], None)))

      btn_box = BoxLayout(
          orientation="horizontal",
          size_hint_y=None,
          height=38,
          spacing=8,
      )
      btn_wa = Button(
          text="📤 Enviar WhatsApp",
          background_color=(0.2, 0.8, 0.4, 1),
          size_hint_x=0.6,
      )
      btn_wa.bind(
          on_press=lambda inst, combo=c: self.enviar_combo_guardado_wa(combo)
      )

      btn_del = Button(
          text="Eliminar",
          background_color=(1, 0.3, 0.3, 1),
          size_hint_x=0.4,
      )
      btn_del.bind(
          on_press=lambda inst, i=idx: self.confirmar_eliminacion_combo(i)
      )

      btn_box.add_widget(btn_wa)
      btn_box.add_widget(btn_del)

      box.add_widget(lbl_nombre)
      box.add_widget(lbl_items_block)
      box.add_widget(lbl_precio)
      box.add_widget(btn_box)

      self.pantalla_contenido.add_widget(box)

  def enviar_combo_guardado_wa(self, combo):
    tot_usd = combo["total_usd"]
    tot_bs = tot_usd * self.tasa_bcv

    msg = f"*COMERCIALIZADORA HNOS. AGUILERA 2019 C.A*\n"
    msg += f"*RIF: J-41283366-9*\n"
    msg += f"*Presupuesto: {combo['nombre']}*\n\n"
    msg += "Detalle del combo:\n"

    for it in combo["items"]:
      prod_ref = next(
          (
              p
              for p in self.productos
              if p["nombre"].upper() == it["prod"]["nombre"].upper()
          ),
          it["prod"],
      )
      sub_usd = prod_ref["precio_unit_usd"] * it["cantidad"]
      sub_bs = sub_usd * self.tasa_bcv
      msg += f"• {it['cantidad']}x {prod_ref['nombre']} - ${sub_usd:.2f} ({sub_bs:,.2f} Bs)\n"

    msg += f"\n*TOTAL: ${tot_usd:.2f} / {tot_bs:,.2f} Bs*\n"
    msg += f"(Tasa BCV: {self.tasa_bcv} Bs/$)\n\n"
    msg += "¡Estamos a su orden para procesar su pedido!"

    numero = "+584245389751"
    msg_encoded = urllib.parse.quote(msg)
    url = f"https://wa.me/{numero}?text={msg_encoded}"

    webbrowser.open(url)

  def confirmar_eliminacion_combo(self, index):
    if not (0 <= index < len(self.combos_guardados)):
      return
    combo_nombre = self.combos_guardados[index]["nombre"]

    content = BoxLayout(orientation="vertical", padding=15, spacing=15)
    content.add_widget(
        Label(
            text=(
                f"¿Está seguro de eliminar el combo:\n[b]{combo_nombre}[/b]?"
            ),
            markup=True,
            halign="center",
        )
    )

    btn_box = BoxLayout(size_hint_y=None, height=45, spacing=10)
    btn_si = Button(text="Sí, eliminar", background_color=(1, 0.3, 0.3, 1))
    btn_no = Button(text="Cancelar", background_color=(0.5, 0.5, 0.5, 1))
    btn_box.add_widget(btn_si)
    btn_box.add_widget(btn_no)
    content.add_widget(btn_box)

    popup = Popup(
        title="Confirmar Eliminación",
        content=content,
        size_hint=(0.8, 0.35),
        auto_dismiss=True,
    )

    def eliminar(instance):
      del self.combos_guardados[index]
      self.guardar_datos_disco()
      self.mostrar_combos_guardados(None)
      popup.dismiss()

    btn_si.bind(on_press=eliminar)
    btn_no.bind(on_press=popup.dismiss)
    popup.open()

  def mostrar_notificacion(self, titulo, mensaje):
    content = BoxLayout(orientation="vertical", padding=15, spacing=15)
    content.add_widget(Label(text=mensaje, halign="center"))
    btn = Button(text="Aceptar", size_hint_y=None, height=45)
    content.add_widget(btn)

    popup = Popup(
        title=titulo, content=content, size_hint=(0.8, 0.35), auto_dismiss=True
    )
    btn.bind(on_press=popup.dismiss)
    popup.open()


if __name__ == "__main__":
  InventarioApp().run()
