export default function({ parentElement, data }) {
  const button = parentElement.querySelector('button');
  const note = parentElement.querySelector('[role="status"]');
  let disposed = false;
  const urls = new Set();
  const revoke = url => { URL.revokeObjectURL(url); urls.delete(url); };
  button.onclick = async () => {
    if (button.disabled) return;
    button.disabled = true; note.textContent = '正在制作图片…';
    try {
      await document.fonts.ready;
      if (disposed) return;
      const source = URL.createObjectURL(new Blob([data.svg], {type:'image/svg+xml;charset=utf-8'}));
      urls.add(source);
      const img = new Image();
      img.onload = () => {
        revoke(source);
        if (disposed) return;
        const canvas = document.createElement('canvas'); canvas.width = 1080; canvas.height = 1350;
        try {
          canvas.getContext('2d').drawImage(img, 0, 0);
          canvas.toBlob(blob => {
            if (disposed) return;
            if (!blob) { note.textContent = '图片生成失败，可使用下方 SVG 备用下载。'; button.disabled = false; return; }
            const url = URL.createObjectURL(blob); urls.add(url);
            const link = document.createElement('a'); link.href = url; link.download = data.filename; link.click();
            setTimeout(() => revoke(url), 10000);
            note.textContent = '图片已生成，已发起下载；不含私人信息。'; button.disabled = false;
          }, 'image/png');
        } catch { note.textContent = '浏览器未能生成 PNG，可使用 SVG 备用下载。'; button.disabled = false; }
      };
      img.onerror = () => { revoke(source); if (!disposed) { note.textContent = '图片生成失败，可使用 SVG 备用下载。'; button.disabled = false; } };
      img.src = source;
    } catch { if (!disposed) { note.textContent = '请使用下方 SVG 备用下载。'; button.disabled = false; } }
  };
  return () => { disposed = true; button.onclick = null; urls.forEach(revoke); };
}
