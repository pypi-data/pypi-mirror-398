from pyscreeps_arena.compiler import Compiler

if __name__ == '__main__':
    compiler = Compiler('src', 'library', 'build')

    compiler.compile()
    # compiler.clean()