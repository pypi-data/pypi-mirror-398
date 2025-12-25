# Fixing Slow Page Load Times: A Developer's Checklist

Your page loads in 4 seconds. Users leave at 3. Let's fix that.

## Diagnose First

Run Lighthouse. Look at three numbers:

- First Contentful Paint (FCP)
- Largest Contentful Paint (LCP)
- Total Blocking Time (TBT)

If LCP is over 2.5s, that's your priority.

## Quick Wins (Under 30 Minutes)

### Images

90% of slow pages have image problems.

Convert to WebP. Add `loading="lazy"` to images below the fold. Add explicit width/height to prevent layout shift.

### Fonts

Self-host your fonts. Google Fonts adds an extra DNS lookup and connection.

Use `font-display: swap` so text shows immediately.

### Third-Party Scripts

Move analytics and chat widgets to load after the page. They don't need to block rendering.

## If That's Not Enough

Check your server response time. If TTFB is over 200ms:

- Add caching headers
- Use a CDN
- Upgrade your hosting

Measure again. Repeat until LCP is under 2.5s.

## The Bottom Line

Performance isn't about perfection. It's about hitting the thresholds that matter:

- LCP under 2.5s
- FID under 100ms
- CLS under 0.1

Hit those, and you're good enough for Google and good enough for users.
