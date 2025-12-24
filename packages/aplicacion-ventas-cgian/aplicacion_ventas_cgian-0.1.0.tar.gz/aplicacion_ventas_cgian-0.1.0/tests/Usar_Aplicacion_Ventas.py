from aplicacion_ventas.Gestor_Ventas import Gestor_Ventas

def main():
    precio_base: 100.0
    impuesto_porcentaje = 0.05
    descuento_porcentaje = 0.10
    
    gestor = Gestor_Ventas(precio_base,impuesto_porcentaje,descuento_porcentaje)
    precio_final = gestor.calcular_precio_final()
    
    print(f"Precio Base: {precio_base}")
    print(f"Impuesto: {impuesto_porcentaje * 100}%")
    print(f"Descuento: {descuento_porcentaje * 100}%")
    print(f"Precio Final: {precio_final}")


if __name__ == "__main__":
    main()
