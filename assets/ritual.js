export default function({ parentElement, data, setTriggerValue }) {
  const root = parentElement.querySelector('.ritual');
  clearTimeout(root._ritualTimer);
  const coins = root.querySelector('.coins');
  const button = root.querySelector('.toss');
  const title = root.querySelector('.result-title');
  const detail = root.querySelector('.result-detail');
  const reveal = root.querySelector('.reveal');
  const count = data.lines.length;
  const token = `${data.run_id}:${count}`;
  const reduced = data.simple || window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const animate = count > 0 && root.dataset.token !== token && !reduced;
  root.dataset.token = token;
  root.classList.toggle('simple', !!data.simple);
  root.querySelector('.count').textContent = `${String(count).padStart(2, '0')} / 06`;
  let timer;
  // All geometry and inscriptions are local; no personal data enters this DOM.
  const face = (index, back) => {
    const id = `${index}-${back ? 'b' : 'f'}`;
    return `<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg"><defs><radialGradient id="c-${id}" cx="28%" cy="20%" r="88%"><stop stop-color="${back ? '#b8aa83' : '#cbad7c'}"/><stop offset=".48" stop-color="#927654"/><stop offset="1" stop-color="#4f5541"/></radialGradient><mask id="h-${id}"><rect width="100" height="100" fill="white"/><rect x="40" y="40" width="20" height="20" rx="1" fill="black"/></mask></defs><g mask="url(#h-${id})"><circle cx="50" cy="50" r="47" fill="url(#c-${id})" stroke="#aa9770" stroke-width="2"/><circle cx="50" cy="50" r="42" fill="none" stroke="#342e25" stroke-width="1.3"/><circle cx="50" cy="50" r="39" fill="none" stroke="#ddc997" stroke-opacity=".4"/><rect x="36" y="36" width="28" height="28" rx="1" fill="none" stroke="#4e4434" stroke-width="2"/><g fill="#302e24" font-family="serif" font-size="17" text-anchor="middle"><text x="50" y="28">${back ? '观' : '乾'}</text><text x="50" y="86">${back ? '变' : '元'}</text></g><path d="M20 43v14m4-16v18M77 42v16m4-13v10" stroke="#413b2b" stroke-width="2"/><path d="M28 17q20-12 39 1" fill="none" stroke="#f3e1ad" stroke-opacity=".4"/></g></svg>`;
  };
  coins.innerHTML = (data.coins || [3, 3, 3]).map((value, index) => `<div class="coin-slot" style="--side:${value === 2 ? 180 : 0}deg;--rest:${[-13, 4, 17][index]}deg;--delay:${index * 65}ms"><div class="shadow"></div><div class="flight"><div class="rotor"><div class="face">${face(index, false)}</div><div class="face back">${face(index, true)}</div></div></div></div>`).join('');
  const labels = ['初', '二', '三', '四', '五', '上'];
  root.querySelector('.ladder').innerHTML = [5,4,3,2,1,0].map(index => {
    const value = data.lines[index];
    const moving = value === 6 || value === 9;
    return `<div class="yao-row ${animate && index === count - 1 ? 'latest' : ''}" aria-label="${labels[index]}爻：${value || '待投'}"><span class="yao-label">${labels[index]}</span><span class="yao ${value ? '' : 'pending'} ${moving ? 'moving' : ''}"><i></i>${value === 7 || value === 9 ? '' : '<i></i>'}</span></div>`;
  }).join('');
  const settle = () => {
    coins.classList.remove('tossing'); reveal.classList.remove('waiting');
    const value = data.lines[count - 1];
    title.textContent = count ? `${labels[count - 1]}爻 · ${{6:'老阴',7:'少阳',8:'少阴',9:'老阳'}[value]}${value === 6 || value === 9 ? '，变化在此' : '，静中有定'}` : '一念既定，静候变化';
    detail.textContent = count && data.coins ? `${data.coins.join(' + ')} = ${value}　·　${data.coins.map(v => v === 3 ? '正' : '反').join(' / ')}` : '三枚铜钱 · 由下至上';
    button.disabled = count >= 6;
    button.querySelector('span').textContent = count >= 6 ? '六爻已成 · 向下查看解读' : count ? `第 ${count + 1} 次投掷` : '投下三枚铜钱';
  };
  if (animate) {
    button.disabled = true; button.querySelector('span').textContent = '铜钱落定中…';
    title.textContent = '起落之间，变化成形'; detail.textContent = '本次结果已确定，正在呈现';
    reveal.classList.add('waiting'); coins.classList.remove('tossing');
    void coins.offsetWidth; coins.classList.add('tossing'); timer = setTimeout(settle, 1650); root._ritualTimer = timer;
  } else settle();
  button.onclick = () => {
    if (button.disabled || count >= 6) return;
    button.disabled = true; button.querySelector('span').textContent = '正在起卦…';
    // Re-send the same expected index on retry; Python de-duplicates it.
    timer = setTimeout(() => { button.disabled = false; button.querySelector('span').textContent = '连接较慢 · 重试本次投掷'; }, 10000);
    root._ritualTimer = timer;
    setTriggerValue('toss', { run_id: data.run_id, index: count + 1 });
  };
  return () => { clearTimeout(timer); button.onclick = null; };
}
