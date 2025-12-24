export interface CanvasContext {
  canvas: HTMLCanvasElement
  ctx: CanvasRenderingContext2D
  width: number
  height: number
}

export function setupCanvas(container: HTMLElement): CanvasContext {
  const canvas = document.createElement('canvas')
  canvas.style.position = 'absolute'
  canvas.style.top = '0'
  canvas.style.left = '0'
  canvas.style.pointerEvents = 'none'
  container.appendChild(canvas)

  const ctx = canvas.getContext('2d')!

  function resize() {
    canvas.width = container.clientWidth
    canvas.height = container.clientHeight
  }

  resize()
  window.addEventListener('resize', resize)

  return {
    canvas,
    ctx,
    get width() { return canvas.width },
    get height() { return canvas.height }
  }
}

export function clearCanvas(context: CanvasContext): void {
  context.ctx.clearRect(0, 0, context.width, context.height)
}
