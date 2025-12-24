"""
Este es el modulo que incluye la clase de 
reproductor de musica
"""

class Player:
    """
    Esta clase crea un reproductor de musica
    """
    def __init__(self):
        pass  # ← Agregar esto

    def play(self, song):
        """
        Reproduce la cancion que recibio 
        como parametro

        Parametros:
        song (str): este es un string con el path de la cancion

        Returns:
        int: devuelve 1 si hubo un error, 0 si no hubo error
        """
        print("Reproduciendo cancion")

    def stop(self):
        """
        Detiene la cancion que esta reproduciendo
        """
        print("Deteniendo cancion")