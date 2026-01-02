def wrap_text(s: str) -> str:
  """
  Wrap a string with "<string>", 
   remove any leading/trailing whitespaces, 
    and replace inner whitespaces with `+`
  
  :param s: Some string.
  :type s: str
  :return: Copy of the string, formatted as described above.
  :rtype: str
  """
  s = s.strip()
  if ' ' in s:
    return '"' + s.replace(' ', '+') + '"'
  return s